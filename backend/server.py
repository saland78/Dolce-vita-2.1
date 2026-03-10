from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import logging
import asyncio
import traceback
from pathlib import Path
from routes import orders, inventory, auth_routes, customers, settings, webhooks_woocommerce, production
from database import client, db
from services.woocommerce_sync import sync_woocommerce

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

required_vars = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "SECRET_KEY", "MONGO_URL"]
missing_vars = [v for v in required_vars if not os.environ.get(v)]
if missing_vars:
    logging.error(f"CRITICAL: Missing required environment variables: {', '.join(missing_vars)}")

# Disable /docs and /redoc in production
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
docs_url = "/docs" if ENVIRONMENT == "development" else None
redoc_url = "/redoc" if ENVIRONMENT == "development" else None

app = FastAPI(
    title="BakeryOS API",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url="/openapi.json" if ENVIRONMENT == "development" else None
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full details server-side, never expose internals to client
    logger.error(f"Global Exception on {request.url.path}: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )

allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
app_url = os.environ.get('APP_URL')
if app_url and app_url not in allowed_origins:
    allowed_origins.append(app_url)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Cookie"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    # Fix proxy headers for HTTPS
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto
    response = await call_next(request)
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

api_router = APIRouter(prefix="/api")
api_router.include_router(orders.router)
api_router.include_router(inventory.router)
api_router.include_router(auth_routes.router)
api_router.include_router(customers.router)
api_router.include_router(settings.router)
api_router.include_router(webhooks_woocommerce.router)
api_router.include_router(production.router)

@api_router.get("/")
async def root():
    return {"message": "BakeryOS API is running", "status": "ok"}

app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    try:
        await db.oauth_states.create_index("created_at", expireAfterSeconds=600)
        # Index per scadenza sessioni
        await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
    except:
        pass
    asyncio.create_task(sync_woocommerce())

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
