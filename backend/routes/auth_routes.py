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

# --- ROUTES ---

@router.get("/login")
async def login(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    if not redirect_uri:
        logger.error("GOOGLE_REDIRECT_URI is missing in env")
        return Response("Internal Config Error: Missing Redirect URI", status_code=500)

    # 1. Generate Secure State
    state = generate_state()
    
    # 2. Store in DB
    await store_state(db, state)
    
    logger.info(f"Initiating Login. State generated: {state[:8]}... RedirectURI: {redirect_uri}")
    
    client = oauth.create_client('google')
    
    # --- C. FIX: Correct API usage for authlib ---
    # create_authorization_url returns 'dict' in some versions or 'str'?
    # It turns out 'create_authorization_url' on the Starlette client returns the JSON response dict 
    # OR calls the underlying OAuth2Session which returns (url, state).
    # BUT, 'authorize_redirect' handles all of this.
    # Since I want manual state control, I should use the underlying library feature
    # OR simpler: Use 'authorize_redirect' but force the state I want?
    # NO, 'authorize_redirect' stores state in session, which is what we want to avoid.
    
    # We must use 'create_authorization_url'.
    # In Authlib 1.x Starlette client, let's verify what it returns.
    # It delegates to 'framework.client.OAuthClient.create_authorization_url'
    # which returns 'url' (string) usually.
    
    resp = await client.create_authorization_url(redirect_uri, state=state)
    # resp is likely just the URL string or a response object?
    # Actually, looking at source code: it calls OAuth2Session.create_authorization_url
    # OAuth2Session returns (url, state).
    # BUT, client.create_authorization_url might extract just the URL?
    
    # Let's assume it returns just the URL or unpack based on inspection.
    # Wait, the error was "too many values to unpack (expected 2)".
    # This means 'resp' was NOT a tuple of 2. It was likely a single string.
    
    uri = resp['url'] if isinstance(resp, dict) else resp
    
    return RedirectResponse(uri)

@router.get("/callback")
async def auth_callback(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    # ... (Same logic as before, wrapped in robust try/except) ...
    # D. ROBUST ERROR HANDLING
    try:
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
            return RedirectResponse(url="/login?error=invalid_state")

        # 3. Exchange Code for Token
        client = oauth.create_client('google')
        redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
        
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

        # 5. Process User
        google_sub = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        
        if not email:
            raise Exception("Email not provided by Google")

        # User Matching & Creation (Same as before)
        user = await db.users.find_one({"google_sub": google_sub}, {"_id": 0})
        if not user:
            user = await db.users.find_one({"email": email}, {"_id": 0})
            if user:
                await db.users.update_one({"email": email}, {"$set": {"google_sub": google_sub}})
        
        bakery_id = None
        if not user:
            # Register
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
            # Login
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
