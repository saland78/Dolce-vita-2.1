from fastapi import APIRouter, HTTPException, Response, Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import os
import uuid
import requests
from database import get_db
from models import User, UserRole, Bakery

router = APIRouter(prefix="/auth", tags=["auth"])

class SessionData(BaseModel):
    session_id: str

@router.post("/session")
async def exchange_session(data: SessionData, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    EXCHANGE EMERGENT SESSION (Preview Compatible)
    """
    session_id = data.session_id
    
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
    # Emergent doesn't give 'sub' directly sometimes, rely on email or id
    google_sub = user_data.get("id") or email 
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by auth provider")

    # Find or Create User & Bakery
    user = await db.users.find_one({"email": email}, {"_id": 0})
    bakery_id = None
    
    if not user:
        # Create Bakery
        new_bakery = Bakery(
            name=f"Pasticceria di {name.split()[0]}",
            owner_user_id="temp",
            created_at=datetime.now(timezone.utc)
        )
        bakery_res = await db.bakeries.insert_one(new_bakery.model_dump(by_alias=True))
        bakery_id = str(bakery_res.inserted_id)

        new_user = User(
            email=email,
            name=name,
            picture=picture,
            role=UserRole.ADMIN,
            bakery_id=bakery_id,
            google_sub=google_sub
        )
        await db.bakeries.update_one({"_id": bakery_res.inserted_id}, {"$set": {"owner_user_id": new_user.user_id}})
        
        user_dict = new_user.model_dump()
        await db.users.insert_one(user_dict)
        user = user_dict
    else:
        # Update Profile
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture}}
        )
        bakery_id = user.get("bakery_id")

    # Create Session
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "bakery_id": bakery_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })

    # Set Cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True, 
        samesite="none", # 'none' works best in Preview/iFrame
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
        
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user

@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
        
    response.delete_cookie(key="session_token")
    return {"message": "Logged out"}
