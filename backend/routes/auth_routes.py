from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta, timezone
import os, uuid, secrets, requests
from database import get_db
from models import User, UserRole, Bakery

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Rate limiting semplice in memoria
_login_attempts = {}

def check_rate_limit(ip: str) -> bool:
    """Max 10 tentativi di login per IP negli ultimi 5 minuti."""
    now = datetime.now(timezone.utc)
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if (now - t).seconds < 300]
    if len(attempts) >= 10:
        return False
    attempts.append(now)
    _login_attempts[ip] = attempts
    return True

@router.get("/google")
async def google_login(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    client_ip = request.headers.get("x-forwarded-for", request.client.host)
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Troppi tentativi. Riprova tra qualche minuto.")
    
    # CSRF state token
    state = secrets.token_urlsafe(32)
    await db.oauth_states.insert_one({
        "state": state,
        "created_at": datetime.now(timezone.utc)
    })
    
    scope = "openid email profile"
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&state={state}"
    )
    return RedirectResponse(url)

@router.get("/callback")
async def google_callback(
    code: str,
    state: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Verifica CSRF state
    if not state:
        raise HTTPException(status_code=400, detail="Missing state parameter")
    
    stored_state = await db.oauth_states.find_one_and_delete({"state": state})
    if not stored_state:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    token_resp = requests.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    google_sub = user_info.get("id")

    if not email:
        raise HTTPException(status_code=400, detail="Email not provided")

    user = await db.users.find_one({"email": email}, {"_id": 0})
    bakery_id = None

    if not user:
        new_bakery = Bakery(
            name=f"Pasticceria di {name.split()[0]}",
            owner_user_id="temp",
            created_at=datetime.now(timezone.utc)
        )
        bakery_res = await db.bakeries.insert_one(new_bakery.model_dump(by_alias=True))
        bakery_id = str(bakery_res.inserted_id)
        new_user = User(
            email=email, name=name, picture=picture,
            role=UserRole.ADMIN, bakery_id=bakery_id, google_sub=google_sub
        )
        await db.bakeries.update_one(
            {"_id": bakery_res.inserted_id},
            {"$set": {"owner_user_id": new_user.user_id}}
        )
        user_dict = new_user.model_dump()
        await db.users.insert_one(user_dict)
        user = user_dict
    else:
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture}}
        )
        bakery_id = user.get("bakery_id")

    session_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "bakery_id": bakery_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })

    redirect = RedirectResponse(url="/", status_code=302)
    redirect.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7*24*60*60,
        path="/"
    )
    return redirect

@router.get("/me")
async def get_current_user(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Controllo scadenza
    expires_at = session.get("expires_at")
    if expires_at and datetime.now(timezone.utc) > expires_at.replace(tzinfo=timezone.utc) if expires_at.tzinfo is None else expires_at:
        await db.user_sessions.delete_one({"session_token": session_token})
        raise HTTPException(status_code=401, detail="Session expired")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user

@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}
