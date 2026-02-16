from fastapi import APIRouter, HTTPException, Response, Request, Depends
from starlette.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import os
import uuid
import json
from database import get_db
from models import User, UserRole, Bakery

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth Setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/login")
async def login(request: Request):
    # Standard Google OAuth Redirect
    # Ensure redirect_uri matches exactly what you set in Google Console
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'https://pasticceria.andreasalardi.it/api/auth/callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def auth_callback(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            # Try parsing ID Token if userinfo is missing from token response (common in OIDC)
            user_info = await oauth.google.parse_id_token(request, token)
            
    except Exception as e:
        # Log error technically
        print(f"OAuth Error: {e}")
        return RedirectResponse(url="/login?error=oauth_failed")

    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    # --- SaaS Logic: Find or Create User/Bakery ---
    
    user = await db.users.find_one({"email": email}, {"_id": 0})
    bakery_id = None
    
    if not user:
        # NEW USER -> Create Bakery
        new_bakery = Bakery(
            name=f"Pasticceria di {name.split()[0]}",
            owner_user_id="temp",
            # No default keys for security, user must add them in Settings
            created_at=datetime.now(timezone.utc)
        )
        bakery_res = await db.bakeries.insert_one(new_bakery.model_dump(by_alias=True))
        bakery_id = str(bakery_res.inserted_id)

        new_user = User(
            email=email,
            name=name,
            picture=picture,
            role=UserRole.ADMIN,
            bakery_id=bakery_id
        )
        # Link owner
        await db.bakeries.update_one({"_id": bakery_res.inserted_id}, {"$set": {"owner_user_id": new_user.user_id}})
        
        user_dict = new_user.model_dump()
        await db.users.insert_one(user_dict)
        user = user_dict
    else:
        # Existing User -> Update Profile
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture}}
        )
        bakery_id = user.get("bakery_id")

    # --- Session Creation ---
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "bakery_id": bakery_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })

    # Redirect to Frontend Root
    response = RedirectResponse(url="/")
    
    # Set Secure Cookie
    # IMPORTANT: Domain should be omitted to allow subdomains OR set strictly if needed.
    # For 'pasticceria.andreasalardi.it', omitting domain usually defaults to host.
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True, 
        samesite="lax", # Lax is better for top-level navigation redirect
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    return response

@router.get("/me")
async def get_current_user(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
        
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": session_token})
        raise HTTPException(status_code=401, detail="Session expired")
        
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user

@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
        
    response.delete_cookie(key="session_token")
    return {"message": "Logged out"}
