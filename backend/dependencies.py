from fastapi import Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_db
from datetime import datetime, timezone

async def get_current_user_and_bakery(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Controllo scadenza sessione
    expires_at = session.get("expires_at")
    if expires_at:
        exp = expires_at.replace(tzinfo=timezone.utc) if expires_at.tzinfo is None else expires_at
        if datetime.now(timezone.utc) > exp:
            await db.user_sessions.delete_one({"session_token": session_token})
            raise HTTPException(status_code=401, detail="Session expired")
        
    bakery_id = session.get("bakery_id")
    if not bakery_id:
        user = await db.users.find_one({"user_id": session["user_id"]})
        if user and user.get("bakery_id"):
            bakery_id = user["bakery_id"]
        else:
            raise HTTPException(status_code=400, detail="User has no associated bakery")
            
    return session["user_id"], bakery_id
