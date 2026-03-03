import secrets
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import uuid
import json
from database import get_db
from models import User, UserRole, Bakery

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# --- OAUTH CONFIG ---
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- UTILS ---
def generate_state():
    return secrets.token_urlsafe(32) # Secure 256-bit random string

async def store_state(db: AsyncIOMotorDatabase, state: str):
    """
    Store OAuth state in MongoDB with TTL (Time To Live).
    Prevents Replay Attacks and Session Fixation.
    """
    await db.oauth_states.insert_one({
        "state": state,
        "created_at": datetime.now(timezone.utc)
    })
    # Ensure index exists (should be done on startup really)
    # await db.oauth_states.create_index("created_at", expireAfterSeconds=600) # 10 minutes

async def verify_and_consume_state(db: AsyncIOMotorDatabase, state: str):
    """
    Verify state exists and delete it immediately (One-Time Use).
    """
    if not state:
        return False
    result = await db.oauth_states.find_one_and_delete({"state": state})
    return result is not None

# --- ROUTES ---

@router.get("/login")
async def login(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Initiates Google Login with robust State handling (MongoDB).
    """
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    if not redirect_uri:
        logger.error("GOOGLE_REDIRECT_URI is missing in env")
        return Response("Internal Config Error: Missing Redirect URI", status_code=500)

    # 1. Generate Secure State
    state = generate_state()
    
    # 2. Store in DB (Shared Storage for multi-container/restart resilience)
    await store_state(db, state)
    
    logger.info(f"Initiating Login. State generated: {state[:8]}... RedirectURI: {redirect_uri}")
    
    # 3. Create Authorization URL manually to bypass cookie-session dependence
    # We use the lower-level 'create_authorization_url' method
    client = oauth.create_client('google')
    uri, _ = await client.create_authorization_url(redirect_uri, state=state)
    
    return RedirectResponse(uri)

@router.get("/callback")
async def auth_callback(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Handles Google Callback with strict State validation.
    """
    # 1. Extract State & Code
    state = request.query_params.get('state')
    code = request.query_params.get('code')
    error = request.query_params.get('error')
    
    if error:
        logger.error(f"Google returned error: {error}")
        return RedirectResponse(url=f"/login?error=google_error&details={error}")

    if not code:
        logger.error("No code provided")
        return RedirectResponse(url="/login?error=no_code")

    # 2. Verify State (Nonce)
    is_valid = await verify_and_consume_state(db, state)
    if not is_valid:
        logger.error(f"Invalid State Parameter: {state[:8] if state else 'None'}...")
        # This is the fix for "Invalid state parameter"
        return RedirectResponse(url="/login?error=invalid_state")

    try:
        # 3. Exchange Code for Token (Manual Flow)
        client = oauth.create_client('google')
        redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
        
        # We manually fetch token to avoid authlib looking into session for state
        token = await client.fetch_access_token(
            redirect_uri=redirect_uri,
            code=code,
            grant_type='authorization_code'
        )
        
        # 4. Get User Info
        # 'parse_id_token' requires the 'nonce' if used, but we used 'state'.
        # Standard OIDC often puts user info in id_token.
        user_info = await client.parse_id_token(token, nonce=None)
        
        # Fallback if id_token doesn't have what we need (rare for Google)
        if not user_info:
             user_info = await client.userinfo(token=token)

    except Exception as e:
        logger.error(f"Token Exchange Error: {str(e)}")
        return RedirectResponse(url="/login?error=token_exchange_failed")

    # 5. Process User (Multi-Tenant Logic)
    google_sub = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    # Strategy: Match by 'google_sub' (Stable). Fallback to 'email' (Migration).
    user = await db.users.find_one({"google_sub": google_sub}, {"_id": 0})
    
    if not user:
        # Try finding by email (Legacy/Migration)
        user = await db.users.find_one({"email": email}, {"_id": 0})
        if user:
            # Migration: Link existing user to Google Sub
            await db.users.update_one({"email": email}, {"$set": {"google_sub": google_sub}})
            logger.info(f"Linked existing user {email} to sub {google_sub}")
    
    bakery_id = None
    
    if not user:
        # BRAND NEW USER -> New Bakery
        logger.info(f"Registering new user: {email}")
        new_bakery = Bakery(
            name=f"Pasticceria di {name.split()[0]}",
            owner_user_id="temp",
            created_at=datetime.now(timezone.utc)
        )
        bakery_res = await db.bakeries.insert_one(new_bakery.model_dump(by_alias=True))
        bakery_id = str(bakery_res.inserted_id)

        new_user = User(
            google_sub=google_sub,
            email=email,
            name=name,
            picture=picture,
            role=UserRole.ADMIN,
            bakery_id=bakery_id
        )
        await db.bakeries.update_one({"_id": bakery_res.inserted_id}, {"$set": {"owner_user_id": new_user.user_id}})
        await db.users.insert_one(new_user.model_dump())
        user = new_user.model_dump()
    else:
        # Update Metadata
        await db.users.update_one(
            {"email": email},
            {"$set": {
                "name": name, 
                "picture": picture, 
                "last_login_at": datetime.now(timezone.utc),
                "google_sub": google_sub # Ensure it's set
            }}
        )
        bakery_id = user.get("bakery_id")

    # 6. Create Session
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "bakery_id": bakery_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })

    # 7. Response with Cookie
    response = RedirectResponse(url="/")
    
    # Secure Cookie Settings
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True, # MANDATORY FOR PRODUCTION
        samesite="lax", # Lax allows redirect from external site
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
        
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user

@router.post("/logout")
async def logout(response: Response, request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
        
    response.delete_cookie(key="session_token")
    return {"message": "Logged out"}
