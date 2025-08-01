from fastapi import FastAPI, APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import json
import asyncio
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Store active sessions and SSE connections for real-time updates
active_rooms: Dict[str, Dict] = {}
user_sessions: Dict[str, Dict] = {}
sse_connections: Dict[str, asyncio.Queue] = {}

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

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

class CodeUpdate(BaseModel):
    room_id: str
    code: str
    user_id: str

class CursorUpdate(BaseModel):
    room_id: str
    user_id: str
    position: Dict[str, int]

class JoinRoomRequest(BaseModel):
    room_id: str
    user_id: str

# Utility functions for SSE
async def send_to_room(room_id: str, event_type: str, data: dict, exclude_user: str = None):
    """Send an event to all users in a room via SSE"""
    if room_id in active_rooms:
        for user_id, user_data in active_rooms[room_id]["users"].items():
            if exclude_user and user_id == exclude_user:
                continue
            
            if user_id in sse_connections:
                event_data = {
                    "type": event_type,
                    "data": data
                }
                try:
                    await sse_connections[user_id].put(json.dumps(event_data))
                except:
                    # Remove broken connection
                    if user_id in sse_connections:
                        del sse_connections[user_id]

async def generate_sse_stream(user_id: str):
    """Generate SSE stream for a user"""
    queue = asyncio.Queue()
    sse_connections[user_id] = queue
    
    try:
        while True:
            try:
                # Wait for new messages with timeout
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {message}\n\n"
            except asyncio.TimeoutError:
                # Send keep-alive ping
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
            except Exception as e:
                break
    finally:
        if user_id in sse_connections:
            del sse_connections[user_id]

# API Routes
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

@api_router.post("/rooms/join")
async def join_room(request: JoinRoomRequest):
    room_id = request.room_id
    user_id = request.user_id
    
    # Check if room exists in database
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        return {"error": "Room not found"}
    
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
    user_data = {"user_id": user_id}
    active_rooms[room_id]["users"][user_id] = user_data
    user_sessions[user_id] = {"room_id": room_id}
    
    # Notify other users
    await send_to_room(room_id, "user_joined", {
        "user_id": user_id,
        "users": list(active_rooms[room_id]["users"].values())
    }, exclude_user=user_id)
    
    return {
        "room_id": room_id,
        "room_name": active_rooms[room_id]["name"],
        "code": active_rooms[room_id]["code"],
        "language": active_rooms[room_id]["language"],
        "user_id": user_id,
        "users": list(active_rooms[room_id]["users"].values())
    }

@api_router.post("/rooms/code")
async def update_code(update: CodeUpdate):
    room_id = update.room_id
    user_id = update.user_id
    new_code = update.code
    
    if room_id not in active_rooms:
        return {"error": "Room not found"}
    
    # Update code in room
    active_rooms[room_id]["code"] = new_code
    
    # Update in database
    await db.rooms.update_one(
        {"id": room_id},
        {"$set": {"code": new_code}}
    )
    
    # Broadcast to other users
    await send_to_room(room_id, "code_updated", {
        "code": new_code,
        "user_id": user_id
    }, exclude_user=user_id)
    
    return {"success": True}

@api_router.post("/rooms/cursor")
async def update_cursor(update: CursorUpdate):
    room_id = update.room_id
    user_id = update.user_id
    position = update.position
    
    if room_id not in active_rooms:
        return {"error": "Room not found"}
    
    # Update cursor position
    active_rooms[room_id]["cursors"][user_id] = {
        "user_id": user_id,
        "position": position
    }
    
    # Broadcast cursor position
    await send_to_room(room_id, "cursor_updated", {
        "user_id": user_id,
        "position": position
    }, exclude_user=user_id)
    
    return {"success": True}

@api_router.post("/rooms/{room_id}/save")
async def save_room(room_id: str):
    if room_id not in active_rooms:
        return {"error": "Room not found"}
    
    # Save current code to database
    current_code = active_rooms[room_id]["code"]
    await db.rooms.update_one(
        {"id": room_id},
        {"$set": {"code": current_code, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "File saved successfully"}

@api_router.get("/sse/{user_id}")
async def sse_endpoint(user_id: str):
    """Server-Sent Events endpoint for real-time updates"""
    return StreamingResponse(
        generate_sse_stream(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# Include the router in the main app
app.include_router(api_router)

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

# Cleanup function to remove disconnected users
async def cleanup_disconnected_users():
    """Background task to clean up disconnected users"""
    while True:
        try:
            for room_id, room_data in list(active_rooms.items()):
                users_to_remove = []
                for user_id in list(room_data["users"].keys()):
                    if user_id not in sse_connections:
                        users_to_remove.append(user_id)
                
                for user_id in users_to_remove:
                    if user_id in room_data["users"]:
                        del room_data["users"][user_id]
                    if user_id in room_data["cursors"]:
                        del room_data["cursors"][user_id]
                    if user_id in user_sessions:
                        del user_sessions[user_id]
                    
                    # Notify remaining users
                    await send_to_room(room_id, "user_left", {
                        "user_id": user_id,
                        "users": list(room_data["users"].values())
                    })
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(30)

# Start cleanup task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_disconnected_users())