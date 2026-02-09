from fastapi import APIRouter, HTTPException, Response, Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import os
import uuid
import requests
from database import get_db
from models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

class SessionData(BaseModel):
    session_id: str

@router.post("/session")
async def exchange_session(data: SessionData, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Exchanges the temporary session_id from Emergent Auth for a persistent session token.
    """
    session_id = data.session_id
    
    # 1. Call Emergent Auth to get user data
    # IMPORTANT: This call must be from backend
    try:
        emergent_resp = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id},
            timeout=10
        )
        emergent_resp.raise_for_status()
        user_data = emergent_resp.json()
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid session: {str(e)}")

    email = user_data.get("email")
    name = user_data.get("name")
    picture = user_data.get("picture")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by auth provider")

    # 2. Find or Create User
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not user:
        # Create new user
        new_user = User(
            email=email,
            name=name,
            picture=picture,
            role=UserRole.ADMIN # Default to admin for MVP convenience
        )
        user_dict = new_user.model_dump()
        await db.users.insert_one(user_dict)
        user = user_dict
    else:
        # Update existing user info if needed
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture}}
        )

    # 3. Create Session
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })

    # 4. Set Cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True, # Critical for HTTPS
        samesite="none", # Critical for cross-site if needed, or lax/strict
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    return user

@router.get("/me")
async def get_current_user(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
        
    # Check expiry
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": session_token})
        raise HTTPException(status_code=401, detail="Session expired")
        
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user

@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
        
    response.delete_cookie(key="session_token")
    return {"message": "Logged out"}
