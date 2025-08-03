from fastapi import FastAPI, APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exception_handlers import http_exception_handler
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
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
import httpx
import traceback

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import robust MongoDB configuration
from mongo_config import mongo_config

# MongoDB will be initialized in startup event
db = None

# Store active sessions and SSE connections for real-time updates
active_rooms: Dict[str, Dict] = {}
user_sessions: Dict[str, Dict] = {}
sse_connections: Dict[str, asyncio.Queue] = {}

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(
    title="CodeSync API",
    description="Real-time collaborative code editor backend",
    version="1.0.0"
)

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
    user_name: Optional[str] = None

class CursorUpdate(BaseModel):
    room_id: str
    user_id: str
    user_name: Optional[str] = None
    position: Dict[str, int]

class JoinRoomRequest(BaseModel):
    room_id: str
    user_id: str
    user_name: str

class RunCodeRequest(BaseModel):
    language: str
    code: str
    stdin: Optional[str] = ""

class RunCodeResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    error: Optional[str] = None

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str
    user_id: str
    user_name: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SendChatMessageRequest(BaseModel):
    room_id: str
    user_id: str
    user_name: str
    message: str

class TypingStatusRequest(BaseModel):
    room_id: str
    user_id: str
    user_name: str
    is_typing: bool

class LeaveRoomRequest(BaseModel):
    room_id: str
    user_id: str
    user_name: str

# Utility functions for SSE
async def send_to_room(room_id: str, event_type: str, data: dict, exclude_user: str = None):
    """Send an event to all users in a room via SSE"""
    logger.info(f"Broadcasting {event_type} event to room {room_id} (excluding user: {exclude_user})")
    
    if room_id in active_rooms:
        recipients = 0
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
                    recipients += 1
                except:
                    # Remove broken connection
                    logger.warning(f"Removing broken SSE connection for user: {user_id}")
                    if user_id in sse_connections:
                        del sse_connections[user_id]
        
        logger.info(f"Event {event_type} sent to {recipients} users in room {room_id}")
    else:
        logger.warning(f"Attempted to send event to non-existent room: {room_id}")

async def generate_sse_stream(user_id: str):
    """Generate SSE stream for a user"""
    queue = asyncio.Queue()
    sse_connections[user_id] = queue
    logger.info(f"SSE stream started for user: {user_id}")
    
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
                logger.error(f"SSE stream error for user {user_id}: {e}")
                break
    finally:
        logger.info(f"SSE stream ended for user: {user_id}")
        if user_id in sse_connections:
            del sse_connections[user_id]

# Root Routes (without /api prefix)
@app.get("/")
async def root():
    """Root endpoint for health checks and basic API information"""
    logger.info("Root endpoint accessed")
    return {
        "message": "CodeSync Real-Time Code Editor Backend",
        "status": "running",
        "version": "1.0.0",
        "api_docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring systems"""
    logger.info("Health check endpoint accessed")
    
    # Check MongoDB health using the new config
    db_status = "disconnected"
    if await mongo_config.health_check():
        db_status = "connected"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "active_rooms": len(active_rooms),
        "active_connections": len(sse_connections)
    }

# Custom exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    logger.warning(f"404 Not Found: {request.method} {request.url}")
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": f"The requested endpoint {request.url.path} was not found",
            "method": request.method,
            "available_endpoints": ["/", "/health", "/api/", "/docs"]
        }
    )

@app.exception_handler(400)
async def bad_request_handler(request: Request, exc: HTTPException):
    logger.warning(f"400 Bad Request: {request.method} {request.url} - {exc.detail}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Bad Request",
            "detail": str(exc.detail),
            "method": request.method,
            "url": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.error(f"500 Internal Server Error: {request.method} {request.url} - {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "method": request.method,
            "url": str(request.url)
        }
    )

# API Routes
@api_router.get("/")
async def api_root():
    logger.info("API root endpoint accessed")
    return {"message": "Real-Time Code Editor API", "endpoints": "/docs"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    logger.info(f"Creating status check for client: {input.client_name}")
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    logger.info(f"Status check created with ID: {status_obj.id}")
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/rooms", response_model=Room)
async def create_room(room_data: RoomCreate):
    logger.info(f"Creating room: {room_data.name} with language: {room_data.language}")
    try:
        room = Room(name=room_data.name, language=room_data.language)
        room_dict = room.dict()
        
        # Test database connection before operation
        await db.command("ping")
        
        await db.rooms.insert_one(room_dict)
        
        # Initialize room in memory
        active_rooms[room.id] = {
            "name": room.name,
            "code": "",
            "language": room.language,
            "users": {},
            "cursors": {},
            "chat_messages": [],
            "typing_users": {}
        }
        
        logger.info(f"Room created successfully with ID: {room.id}")
        return room
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Database connection error when creating room: {str(e)}")
        raise HTTPException(status_code=503, detail="Database connection error")
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.options("/rooms")
async def create_room_options():
    logger.info("OPTIONS request received for /api/rooms")
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@api_router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    logger.info(f"Getting room details for room_id: {room_id}")
    room = await db.rooms.find_one({"id": room_id})
    if room:
        logger.info(f"Room found: {room_id}")
        return room
    logger.warning(f"Room not found: {room_id}")
    return {"error": "Room not found"}

@api_router.post("/rooms/join")
async def join_room(request: JoinRoomRequest):
    room_id = request.room_id
    user_id = request.user_id
    user_name = request.user_name
    
    logger.info(f"User {user_name} ({user_id}) attempting to join room: {room_id}")
    
    # Check if room exists in database
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        logger.warning(f"Room not found in database: {room_id}")
        return {"error": "Room not found"}
    
    # Initialize room in memory if not exists
    if room_id not in active_rooms:
        logger.info(f"Initializing room in memory: {room_id}")
        active_rooms[room_id] = {
            "name": room["name"],
            "code": room.get("code", ""),
            "language": room["language"],
            "users": {},
            "cursors": {},
            "chat_messages": [],
            "typing_users": {}
        }
    
    # Add user to room with name
    user_data = {"user_id": user_id, "user_name": user_name}
    active_rooms[room_id]["users"][user_id] = user_data
    user_sessions[user_id] = {"room_id": room_id, "user_name": user_name}
    
    logger.info(f"User {user_name} successfully joined room {room_id}. Total users: {len(active_rooms[room_id]['users'])}")
    
    # Notify other users
    await send_to_room(room_id, "user_joined", {
        "user_id": user_id,
        "user_name": user_name,
        "users": list(active_rooms[room_id]["users"].values())
    }, exclude_user=user_id)
    
    return {
        "room_id": room_id,
        "room_name": active_rooms[room_id]["name"],
        "code": active_rooms[room_id]["code"],
        "language": active_rooms[room_id]["language"],
        "user_id": user_id,
        "user_name": user_name,
        "users": list(active_rooms[room_id]["users"].values()),
        "chat_messages": active_rooms[room_id]["chat_messages"]
    }

@api_router.post("/rooms/code")
async def update_code(update: CodeUpdate):
    room_id = update.room_id
    user_id = update.user_id
    user_name = update.user_name
    new_code = update.code
    
    if room_id not in active_rooms:
        return {"error": "Room not found"}
    
    # Get user name from session if not provided
    if not user_name and user_id in user_sessions:
        user_name = user_sessions[user_id].get("user_name", user_id)
    
    # Update code in room
    active_rooms[room_id]["code"] = new_code
    
    # Update in database
    await db.rooms.update_one(
        {"id": room_id},
        {"$set": {"code": new_code}}
    )
    
    # Broadcast to other users with user name
    await send_to_room(room_id, "code_updated", {
        "code": new_code,
        "user_id": user_id,
        "user_name": user_name or user_id
    }, exclude_user=user_id)
    
    return {"success": True}

@api_router.post("/rooms/cursor")
async def update_cursor(update: CursorUpdate):
    room_id = update.room_id
    user_id = update.user_id
    user_name = update.user_name
    position = update.position
    
    if room_id not in active_rooms:
        return {"error": "Room not found"}
    
    # Get user name from session if not provided
    if not user_name and user_id in user_sessions:
        user_name = user_sessions[user_id].get("user_name", user_id)
    
    # Update cursor position with user name
    active_rooms[room_id]["cursors"][user_id] = {
        "user_id": user_id,
        "user_name": user_name or user_id,
        "position": position
    }
    
    # Broadcast cursor position with user name
    await send_to_room(room_id, "cursor_updated", {
        "user_id": user_id,
        "user_name": user_name or user_id,
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

@api_router.post("/send-chat-message")
async def send_chat_message(request: SendChatMessageRequest):
    """Send a chat message to a room"""
    room_id = request.room_id
    user_id = request.user_id
    user_name = request.user_name
    message = request.message.strip()
    
    logger.info(f"Chat message from {user_name} ({user_id}) in room {room_id}: {len(message)} chars")
    
    # Validate input
    if not message:
        logger.warning(f"Empty message rejected from user {user_id}")
        return {"error": "Message cannot be empty"}
    
    if len(message) > 200:
        logger.warning(f"Message too long rejected from user {user_id}: {len(message)} chars")
        return {"error": "Message too long (max 200 characters)"}
    
    if room_id not in active_rooms:
        logger.warning(f"Chat message to non-existent room: {room_id}")
        return {"error": "Room not found"}
    
    # Create chat message
    chat_message = ChatMessage(
        room_id=room_id,
        user_id=user_id,
        user_name=user_name,
        message=message
    )
    
    # Store message in room's chat history (in-memory)
    active_rooms[room_id]["chat_messages"].append(chat_message.dict())
    
    # Keep only last 100 messages to prevent memory bloat
    if len(active_rooms[room_id]["chat_messages"]) > 100:
        active_rooms[room_id]["chat_messages"] = active_rooms[room_id]["chat_messages"][-100:]
        logger.info(f"Chat history trimmed to 100 messages for room {room_id}")
    
    # Broadcast message to all users in the room
    await send_to_room(room_id, "chat_message", {
        "id": chat_message.id,
        "user_id": user_id,
        "user_name": user_name,
        "message": message,
        "timestamp": chat_message.timestamp.isoformat()
    })
    
    logger.info(f"Chat message broadcasted successfully: {chat_message.id}")
    return {"success": True, "message_id": chat_message.id}

@api_router.post("/typing-status")
async def update_typing_status(request: TypingStatusRequest):
    """Update user typing status in a room"""
    room_id = request.room_id
    user_id = request.user_id
    user_name = request.user_name
    is_typing = request.is_typing
    
    if room_id not in active_rooms:
        return {"error": "Room not found"}
    
    # Update typing status
    if is_typing:
        active_rooms[room_id]["typing_users"][user_id] = {
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.utcnow()
        }
    else:
        # Remove user from typing list
        if user_id in active_rooms[room_id]["typing_users"]:
            del active_rooms[room_id]["typing_users"][user_id]
    
    # Broadcast typing status to other users
    typing_users = list(active_rooms[room_id]["typing_users"].values())
    await send_to_room(room_id, "typing_status", {
        "typing_users": typing_users
    }, exclude_user=user_id)
    
    return {"success": True}

@api_router.post("/leave-room")
async def leave_room(request: LeaveRoomRequest):
    """Allow user to gracefully leave a room"""
    room_id = request.room_id
    user_id = request.user_id
    user_name = request.user_name
    
    if room_id not in active_rooms:
        return {"error": "Room not found"}
    
    # Remove user from all room data structures
    if user_id in active_rooms[room_id]["users"]:
        del active_rooms[room_id]["users"][user_id]
    
    if user_id in active_rooms[room_id]["cursors"]:
        del active_rooms[room_id]["cursors"][user_id]
    
    if user_id in active_rooms[room_id]["typing_users"]:
        del active_rooms[room_id]["typing_users"][user_id]
    
    # Remove from user sessions
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    # Remove SSE connection
    if user_id in sse_connections:
        del sse_connections[user_id]
    
    # Notify remaining users
    await send_to_room(room_id, "user_left", {
        "user_id": user_id,
        "user_name": user_name,
        "users": list(active_rooms[room_id]["users"].values())
    })
    
    return {"success": True, "message": "Left room successfully"}

@api_router.post("/run-code", response_model=RunCodeResponse)
async def run_code(request: RunCodeRequest):
    """Execute code using Piston API"""
    logger.info(f"Code execution request - Language: {request.language}, Code length: {len(request.code)} chars")
    
    try:
        # Map frontend language names to Piston API language names
        language_mapping = {
            "javascript": "javascript",
            "python": "python",
            "cpp": "cpp",
            "typescript": "typescript",
            "html": "html",
            "css": "css"
        }
        
        piston_language = language_mapping.get(request.language, request.language)
        logger.info(f"Using Piston language: {piston_language}")
        
        # Prepare the request payload for Piston API
        piston_payload = {
            "language": piston_language,
            "version": "*",  # Use latest version
            "files": [{
                "content": request.code
            }],
            "stdin": request.stdin or ""
        }
        
        logger.info("Sending request to Piston API...")
        
        # Make request to Piston API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://emkc.org/api/v2/piston/execute",
                json=piston_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"Piston API error: {response.status_code} - {response.text}")
                return RunCodeResponse(
                    stdout="",
                    stderr=f"Piston API error: {response.status_code}",
                    exit_code=1,
                    error=f"API request failed with status {response.status_code}"
                )
            
            result = response.json()
            logger.info(f"Piston API response received: exit_code={result.get('run', {}).get('code', 'unknown')}")
            
            # Extract results from Piston API response
            run_result = result.get("run", {})
            stdout = run_result.get("stdout", "")
            stderr = run_result.get("stderr", "")
            exit_code = run_result.get("code", 0)
            
            logger.info(f"Code execution completed - stdout length: {len(stdout)}, stderr length: {len(stderr)}, exit_code: {exit_code}")
            
            return RunCodeResponse(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code
            )
            
    except httpx.TimeoutException:
        logger.error("Code execution timed out after 30 seconds")
        return RunCodeResponse(
            stdout="",
            stderr="Code execution timed out",
            exit_code=1,
            error="Request timed out after 30 seconds"
        )
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        logger.error(traceback.format_exc())
        return RunCodeResponse(
            stdout="",
            stderr=f"Execution error: {str(e)}",
            exit_code=1,
            error=str(e)
        )

@api_router.options("/run-code")
async def run_code_options():
    logger.info("OPTIONS request received for /api/run-code")
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@api_router.get("/sse/{user_id}")
async def sse_endpoint(user_id: str):
    """Server-Sent Events endpoint for real-time updates"""
    logger.info(f"SSE connection established for user: {user_id}")
    return StreamingResponse(
        generate_sse_stream(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Include the router in the main app
app.include_router(api_router)

# CORS middleware - configure BEFORE including routes and be specific about allowed methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Configure logging
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    if mongo_config.client:
        mongo_config.client.close()

# Cleanup function to remove disconnected users
async def cleanup_disconnected_users():
    """Background task to clean up disconnected users and stale typing indicators"""
    while True:
        try:
            current_time = datetime.utcnow()
            for room_id, room_data in list(active_rooms.items()):
                users_to_remove = []
                for user_id in list(room_data["users"].keys()):
                    if user_id not in sse_connections:
                        users_to_remove.append(user_id)
                
                # Clean up stale typing indicators (older than 10 seconds)
                typing_users_to_remove = []
                for user_id, typing_data in list(room_data.get("typing_users", {}).items()):
                    typing_timestamp = typing_data.get("timestamp")
                    if typing_timestamp and (current_time - typing_timestamp).total_seconds() > 10:
                        typing_users_to_remove.append(user_id)
                
                for user_id in typing_users_to_remove:
                    if user_id in room_data["typing_users"]:
                        del room_data["typing_users"][user_id]
                    
                    # Broadcast updated typing status
                    typing_users = list(room_data["typing_users"].values())
                    await send_to_room(room_id, "typing_status", {
                        "typing_users": typing_users
                    })
                
                for user_id in users_to_remove:
                    user_name = None
                    if user_id in user_sessions:
                        user_name = user_sessions[user_id].get("user_name", user_id)
                        del user_sessions[user_id]
                    
                    if user_id in room_data["users"]:
                        del room_data["users"][user_id]
                    if user_id in room_data["cursors"]:
                        del room_data["cursors"][user_id]
                    if user_id in room_data.get("typing_users", {}):
                        del room_data["typing_users"][user_id]
                    
                    # Notify remaining users with user name
                    await send_to_room(room_id, "user_left", {
                        "user_id": user_id,
                        "user_name": user_name or user_id,
                        "users": list(room_data["users"].values())
                    })
            
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(30)

# Start cleanup task
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    global db
    
    # Initialize MongoDB connection
    connection_success = await mongo_config.connect()
    if connection_success:
        db = mongo_config.get_database()
        logger.info("✅ Database initialized successfully")
    else:
        logger.critical("❌ Failed to connect to MongoDB. Application may not function properly.")
        # Don't exit the application, just log the error
    
    # Start the cleanup task
    asyncio.create_task(cleanup_disconnected_users())