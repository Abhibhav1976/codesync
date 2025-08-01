from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict
import uuid
from datetime import datetime
import socketio
import aiofiles
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode='asgi'
)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Store active sessions and rooms
active_rooms: Dict[str, Dict] = {}
user_sessions: Dict[str, Dict] = {}

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class Room(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str = ""
    language: str = "javascript"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RoomCreate(BaseModel):
    name: str
    language: str = "javascript"

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Real-Time Code Editor API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/rooms", response_model=Room)
async def create_room(room_data: RoomCreate):
    room = Room(name=room_data.name, language=room_data.language)
    room_dict = room.dict()
    await db.rooms.insert_one(room_dict)
    
    # Initialize room in memory
    active_rooms[room.id] = {
        "name": room.name,
        "code": "",
        "language": room.language,
        "users": {},
        "cursors": {}
    }
    
    return room

@api_router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    room = await db.rooms.find_one({"id": room_id})
    if room:
        return room
    return {"error": "Room not found"}

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    user_sessions[sid] = {
        "user_id": f"user_{sid[:8]}",
        "room_id": None,
        "cursor_position": {"line": 0, "column": 0}
    }

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    
    if sid in user_sessions:
        user_data = user_sessions[sid]
        room_id = user_data.get("room_id")
        
        if room_id and room_id in active_rooms:
            # Remove user from room
            if sid in active_rooms[room_id]["users"]:
                del active_rooms[room_id]["users"][sid]
            if sid in active_rooms[room_id]["cursors"]:
                del active_rooms[room_id]["cursors"][sid]
            
            # Notify other users in the room
            await sio.emit("user_left", {
                "user_id": user_data["user_id"],
                "users": list(active_rooms[room_id]["users"].values())
            }, room=room_id)
        
        del user_sessions[sid]

@sio.event
async def join_room(sid, data):
    room_id = data.get("room_id")
    if not room_id:
        await sio.emit("error", {"message": "Room ID is required"}, room=sid)
        return
    
    # Check if room exists in database
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        await sio.emit("error", {"message": "Room not found"}, room=sid)
        return
    
    # Initialize room in memory if not exists
    if room_id not in active_rooms:
        active_rooms[room_id] = {
            "name": room["name"],
            "code": room.get("code", ""),
            "language": room["language"],
            "users": {},
            "cursors": {}
        }
    
    # Add user to room
    await sio.enter_room(sid, room_id)
    user_sessions[sid]["room_id"] = room_id
    
    user_data = {
        "user_id": user_sessions[sid]["user_id"],
        "sid": sid
    }
    active_rooms[room_id]["users"][sid] = user_data
    
    # Send current room state to the user
    await sio.emit("room_joined", {
        "room_id": room_id,
        "room_name": active_rooms[room_id]["name"],
        "code": active_rooms[room_id]["code"],
        "language": active_rooms[room_id]["language"],
        "user_id": user_sessions[sid]["user_id"],
        "users": list(active_rooms[room_id]["users"].values())
    }, room=sid)
    
    # Notify other users in the room
    await sio.emit("user_joined", {
        "user_id": user_sessions[sid]["user_id"],
        "users": list(active_rooms[room_id]["users"].values())
    }, room=room_id, skip_sid=sid)

@sio.event
async def code_change(sid, data):
    if sid not in user_sessions:
        return
    
    room_id = user_sessions[sid]["room_id"]
    if not room_id or room_id not in active_rooms:
        return
    
    # Update code in room
    new_code = data.get("code", "")
    active_rooms[room_id]["code"] = new_code
    
    # Update in database
    await db.rooms.update_one(
        {"id": room_id},
        {"$set": {"code": new_code}}
    )
    
    # Broadcast to other users in the room
    await sio.emit("code_updated", {
        "code": new_code,
        "user_id": user_sessions[sid]["user_id"]
    }, room=room_id, skip_sid=sid)

@sio.event
async def cursor_change(sid, data):
    if sid not in user_sessions:
        return
    
    room_id = user_sessions[sid]["room_id"]
    if not room_id or room_id not in active_rooms:
        return
    
    # Update cursor position
    cursor_data = {
        "user_id": user_sessions[sid]["user_id"],
        "position": data.get("position", {"line": 0, "column": 0})
    }
    
    active_rooms[room_id]["cursors"][sid] = cursor_data
    user_sessions[sid]["cursor_position"] = cursor_data["position"]
    
    # Broadcast cursor position to other users
    await sio.emit("cursor_updated", cursor_data, room=room_id, skip_sid=sid)

@sio.event
async def save_file(sid, data):
    if sid not in user_sessions:
        return
    
    room_id = user_sessions[sid]["room_id"]
    if not room_id or room_id not in active_rooms:
        return
    
    # Save current code to database
    current_code = active_rooms[room_id]["code"]
    await db.rooms.update_one(
        {"id": room_id},
        {"$set": {"code": current_code, "updated_at": datetime.utcnow()}}
    )
    
    await sio.emit("file_saved", {"message": "File saved successfully"}, room=sid)

# Include the router in the main app
app.include_router(api_router)

# Mount Socket.IO app
socket_app = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Create the final app for deployment
app = socket_app