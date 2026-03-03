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
    return secrets.token_urlsafe(32)

async def store_state(db: AsyncIOMotorDatabase, state: str):
    await db.oauth_states.insert_one({
        "state": state,
        "created_at": datetime.now(timezone.utc)
    })

async def verify_and_consume_state(db: AsyncIOMotorDatabase, state: str):
    if not state:
        return False
    result = await db.oauth_states.find_one_and_delete({"state": state})
    return result is not None

def get_redirect_uri():
    """
    Dynamic Redirect URI resolution.
    1. Production: GOOGLE_REDIRECT_URI env var
    2. Preview: APP_URL env var + /api/auth/callback
    """
    env_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    if env_uri:
        return env_uri
        
    app_url = os.environ.get('APP_URL')
    if app_url:
        # Ensure no double slash if APP_URL ends with /
        base = app_url.rstrip('/')
        return f"{base}/api/auth/callback"
        
    return None

# --- ROUTES ---

@router.get("/login")
async def login(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    redirect_uri = get_redirect_uri()
    if not redirect_uri:
        logger.error("Configuration Error: Neither GOOGLE_REDIRECT_URI nor APP_URL are set.")
        return Response("Internal Config Error: Missing Redirect URI configuration", status_code=500)

    # 1. Generate Secure State
    state = generate_state()
    
    # 2. Store in DB
    await store_state(db, state)
    
    logger.info(f"Initiating Login. State: {state[:8]}... URI: {redirect_uri}")
    
    client = oauth.create_client('google')
    
    # 3. Generate URL
    resp = await client.create_authorization_url(redirect_uri, state=state)
    uri = resp['url'] if isinstance(resp, dict) else resp
    
    return RedirectResponse(uri)

@router.get("/callback")
async def auth_callback(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        # 1. Extract
        state = request.query_params.get('state')
        code = request.query_params.get('code')
        error = request.query_params.get('error')
        
        if error:
            logger.error(f"Google returned error: {error}")
            return RedirectResponse(url=f"/login?error=google_error&details={error}")

        if not code:
            logger.error("No code provided")
            return RedirectResponse(url="/login?error=no_code")

        # 2. Verify State
        is_valid = await verify_and_consume_state(db, state)
        if not is_valid:
            logger.error(f"Invalid State Parameter: {state[:8] if state else 'None'}...")
            return RedirectResponse(url="/login?error=invalid_state")

        # 3. Exchange Token
        client = oauth.create_client('google')
        redirect_uri = get_redirect_uri()
        
        token = await client.fetch_access_token(
            redirect_uri=redirect_uri,
            code=code,
            grant_type='authorization_code'
        )
        
        # 4. Get User Info
        try:
            user_info = await client.parse_id_token(token, nonce=None)
        except Exception:
            user_info = await client.userinfo(token=token)

        # 5. Process User (Sync/Create)
        google_sub = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        
        if not email:
            raise Exception("Email not provided by Google")

        user = await db.users.find_one({"google_sub": google_sub}, {"_id": 0})
        if not user:
            user = await db.users.find_one({"email": email}, {"_id": 0})
            if user:
                await db.users.update_one({"email": email}, {"$set": {"google_sub": google_sub}})
        
        bakery_id = None
        if not user:
            # Register New Tenant
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
            # Login Existing
            await db.users.update_one(
                {"email": email},
                {"$set": {"name": name, "picture": picture, "last_login_at": datetime.now(timezone.utc), "google_sub": google_sub}}
            )
            bakery_id = user.get("bakery_id")

        # 6. Session
        session_token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        await db.user_sessions.insert_one({
            "user_id": user["user_id"],
            "bakery_id": bakery_id,
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        })

        response = RedirectResponse(url="/")
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True, 
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/"
        )
        return response

    except Exception as e:
        logger.exception(f"Callback Logic Error: {e}")
        return RedirectResponse(url="/login?error=auth_failed")
