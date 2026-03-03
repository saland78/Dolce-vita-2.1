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

# Load Env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# --- B. ENV VALIDATION ---
required_vars = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "SECRET_KEY", "MONGO_URL"]
missing_vars = [v for v in required_vars if not os.environ.get(v)]
if missing_vars:
    logging.error(f"CRITICAL: Missing required environment variables: {', '.join(missing_vars)}")
    # We don't raise RuntimeError here to allow the container to start and show logs, 
    # but the app will be unstable. Better to crash? 
    # User requested "Se anche una sola manca -> l'app NON parte".
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

app = FastAPI(title="BakeryOS API")

# --- A. GLOBAL EXCEPTION HANDLER ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    # In production, hide details. In dev/preview, showing detail helps.
    # We are in dev/preview mostly.
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc), # Helpful for debug
            "path": request.url.path
        }
    )

allowed_origins = os.environ.get('CORS_ORIGINS', 'https://pasticceria.andreasalardi.it,http://localhost:3000').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def fix_proxy_headers(request: Request, call_next):
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto
    return await call_next(request)

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
        logger.info("Created TTL index for OAuth states")
    except Exception as e:
        logger.warning(f"Could not create index: {e}")
        
    asyncio.create_task(sync_woocommerce())

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
