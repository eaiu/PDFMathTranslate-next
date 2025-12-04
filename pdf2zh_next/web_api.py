"""
FastAPI web server for PDFMathTranslate with multi-user authentication.

This module provides REST API endpoints for:
- User authentication (login, logout, registration)
- File upload and translation
- Settings management
- Translation history
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pdf2zh_next.auth import UserManager, AuthenticationError
from pdf2zh_next.config import ConfigManager
from pdf2zh_next.high_level import do_translate_async_stream

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PDFMathTranslate API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize user manager
user_manager = UserManager()

# In-memory storage for active translation tasks
active_tasks = {}


# Pydantic models for request/response
class SetupRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class TranslationSettings(BaseModel):
    service: str
    lang_from: str = "English"
    lang_to: str = "Simplified Chinese"
    # Add other settings as needed


# Dependency to get current user from token
async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Validate authentication token and return current user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user_data = user_manager.validate_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_data


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure current user is an admin"""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


# Authentication endpoints
@app.get("/api/auth/status")
async def check_auth_status():
    """Check if initial setup is required"""
    return {
        "setup_required": not user_manager.has_users(),
        "version": "2.0.0"
    }


@app.post("/api/auth/setup")
async def initial_setup(request: SetupRequest):
    """Create the first admin user"""
    if user_manager.has_users():
        raise HTTPException(status_code=400, detail="Setup already completed")
    
    try:
        user_manager.create_user(request.username, request.password, is_admin=True)
        token = user_manager.authenticate(request.username, request.password)
        
        return {
            "success": True,
            "token": token,
            "username": request.username,
            "is_admin": True
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return session token"""
    token = user_manager.authenticate(request.username, request.password)
    
    if not token:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Get user info
    user_data = user_manager.validate_token(token)
    
    return {
        "success": True,
        "token": token,
        "username": user_data['username'],
        "is_admin": user_data['is_admin']
    }


@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user), authorization: str = Header(None)):
    """Logout current user"""
    token = authorization.replace("Bearer ", "")
    user_manager.logout(token)
    
    return {"success": True, "message": "Logged out successfully"}


@app.post("/api/auth/register")
async def register_user(request: RegisterRequest, admin_user: dict = Depends(get_admin_user)):
    """Register a new user (admin only)"""
    try:
        user_manager.create_user(request.username, request.password, is_admin=False)
        return {"success": True, "message": f"User '{request.username}' created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/auth/users")
async def list_users(admin_user: dict = Depends(get_admin_user)):
    """List all users (admin only)"""
    try:
        users = user_manager.list_users(admin_user['username'])
        return {"success": True, "users": users}
    except AuthenticationError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.delete("/api/auth/users/{username}")
async def delete_user(username: str, admin_user: dict = Depends(get_admin_user)):
    """Delete a user (admin only)"""
    try:
        user_manager.delete_user(username, admin_user['username'])
        return {"success": True, "message": f"User '{username}' deleted successfully"}
    except (AuthenticationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# Settings endpoints
@app.get("/api/settings")
async def get_settings(current_user: dict = Depends(get_current_user)):
    """Get current user's settings"""
    user_dir = user_manager.get_user_dir(current_user['username'])
    settings_file = user_dir / "settings.json"
    
    if settings_file.exists():
        settings = json.loads(settings_file.read_text())
    else:
        settings = {}
    
    return {"success": True, "settings": settings}


@app.post("/api/settings")
async def update_settings(settings: dict, current_user: dict = Depends(get_current_user)):
    """Update current user's settings"""
    user_dir = user_manager.get_user_dir(current_user['username'])
    settings_file = user_dir / "settings.json"
    
    settings_file.write_text(json.dumps(settings, indent=2))
    
    return {"success": True, "message": "Settings updated successfully"}


@app.post("/api/settings/password")
async def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Change current user's password"""
    try:
        user_manager.change_password(
            current_user['username'],
            request.old_password,
            request.new_password
        )
        return {"success": True, "message": "Password changed successfully"}
    except (AuthenticationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/settings/reset")
async def reset_settings(current_user: dict = Depends(get_current_user)):
    """Reset current user's settings to default"""
    user_dir = user_manager.get_user_dir(current_user['username'])
    settings_file = user_dir / "settings.json"
    
    settings_file.write_text("{}")
    
    return {"success": True, "message": "Settings reset to default"}


# File upload and translation endpoints
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a PDF file for translation"""
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save file to user's upload directory
    user_dir = user_manager.get_user_dir(current_user['username'])
    upload_dir = user_dir / "uploads"
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}_{file.filename}"
    
    # Save uploaded file
    with file_path.open("wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "success": True,
        "file_id": file_id,
        "filename": file.filename,
        "file_path": str(file_path)
    }


@app.post("/api/translate")
async def start_translation(
    file_id: str = Form(...),
    settings: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Start a translation task"""
    # Parse settings
    try:
        translation_settings = json.loads(settings)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid settings JSON")
    
    # Find the uploaded file
    user_dir = user_manager.get_user_dir(current_user['username'])
    upload_dir = user_dir / "uploads"
    
    # Find file with matching file_id
    matching_files = list(upload_dir.glob(f"{file_id}_*"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = matching_files[0]
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create output directory
    output_dir = user_dir / "outputs" / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize task status
    active_tasks[task_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Translation queued",
        "username": current_user['username'],
        "file_id": file_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Start translation in background
    asyncio.create_task(run_translation(task_id, file_path, output_dir, translation_settings, current_user['username']))
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "Translation started"
    }


async def run_translation(task_id: str, file_path: Path, output_dir: Path, settings: dict, username: str):
    """Run translation task in background"""
    try:
        active_tasks[task_id]["status"] = "processing"
        active_tasks[task_id]["message"] = "Translation in progress"
        
        # TODO: Build proper settings from user settings and translation_settings
        # For now, this is a placeholder
        # You'll need to integrate with the existing config system
        
        logger.info(f"Starting translation task {task_id} for user {username}")
        
        # Simulate translation progress
        # In real implementation, integrate with do_translate_async_stream
        for i in range(0, 101, 10):
            await asyncio.sleep(1)
            active_tasks[task_id]["progress"] = i
            active_tasks[task_id]["message"] = f"Translating... {i}%"
        
        # Mark as complete
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 100
        active_tasks[task_id]["message"] = "Translation completed"
        active_tasks[task_id]["output_files"] = {
            "mono": str(output_dir / "translated.pdf"),
            "dual": str(output_dir / "dual.pdf")
        }
        
        # Update user history
        user_dir = user_manager.get_user_dir(username)
        history_file = user_dir / "history.json"
        
        history = json.loads(history_file.read_text()) if history_file.exists() else []
        history.append({
            "task_id": task_id,
            "filename": file_path.name,
            "created_at": active_tasks[task_id]["created_at"],
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        })
        history_file.write_text(json.dumps(history, indent=2))
        
    except Exception as e:
        logger.error(f"Translation task {task_id} failed: {e}", exc_info=True)
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["message"] = f"Translation failed: {str(e)}"


@app.get("/api/translate/status/{task_id}")
async def get_translation_status(task_id: str, current_user: dict = Depends(get_current_user)):
    """Get status of a translation task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    
    # Verify task belongs to current user
    if task["username"] != current_user['username']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"success": True, "task": task}


@app.get("/api/translate/history")
async def get_translation_history(current_user: dict = Depends(get_current_user)):
    """Get current user's translation history"""
    user_dir = user_manager.get_user_dir(current_user['username'])
    history_file = user_dir / "history.json"
    
    if history_file.exists():
        history = json.loads(history_file.read_text())
    else:
        history = []
    
    return {"success": True, "history": history}


@app.get("/api/translate/download/{task_id}")
async def download_translation(
    task_id: str,
    file_type: str = "mono",
    current_user: dict = Depends(get_current_user)
):
    """Download a translated file"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    
    # Verify task belongs to current user
    if task["username"] != current_user['username']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Translation not completed")
    
    # Get file path
    output_files = task.get("output_files", {})
    file_path = output_files.get(file_type)
    
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=Path(file_path).name
    )


# Serve static files (frontend)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("PDFMathTranslate Web API starting...")
    user_manager.cleanup_expired_sessions()
    logger.info("Web API ready")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("PDFMathTranslate Web API shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
