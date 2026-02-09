from fastapi import FastAPI, APIRouter, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from routes import orders, inventory, auth_routes
from database import client

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI(title="BakeryOS API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True, # CRITICAL FOR COOKIES
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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

@api_router.get("/")
async def root():
    return {"message": "BakeryOS API is running", "status": "ok"}

app.include_router(api_router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
