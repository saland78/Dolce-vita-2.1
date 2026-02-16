from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional
from database import get_db
from dependencies import get_current_user_and_bakery
from datetime import datetime, timezone

router = APIRouter(prefix="/settings", tags=["settings"])

class BakerySettingsUpdate(BaseModel):
    name: Optional[str] = None
    wc_url: Optional[str] = None
    wc_consumer_key: Optional[str] = None
    wc_consumer_secret: Optional[str] = None

class BakerySettingsResponse(BaseModel):
    name: str
    wc_url: Optional[str]
    # Do not expose secrets fully in response for security
    has_keys: bool

@router.get("/", response_model=BakerySettingsResponse)
async def get_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    bakery = await db.bakeries.find_one({"_id": bakery_id})
    if not bakery:
        raise HTTPException(status_code=404, detail="Bakery not found")
        
    return {
        "name": bakery["name"],
        "wc_url": bakery.get("wc_url"),
        "has_keys": bool(bakery.get("wc_consumer_key") and bakery.get("wc_consumer_secret"))
    }

@router.put("/", response_model=BakerySettingsResponse)
async def update_settings(
    settings: BakerySettingsUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    update_data = {"updated_at": datetime.now(timezone.utc)}
    if settings.name:
        update_data["name"] = settings.name
    if settings.wc_url:
        update_data["wc_url"] = settings.wc_url.rstrip("/") # normalize
    if settings.wc_consumer_key:
        update_data["wc_consumer_key"] = settings.wc_consumer_key
    if settings.wc_consumer_secret:
        update_data["wc_consumer_secret"] = settings.wc_consumer_secret
        
    await db.bakeries.update_one({"_id": bakery_id}, {"$set": update_data})
    
    # Return updated state
    updated_bakery = await db.bakeries.find_one({"_id": bakery_id})
    return {
        "name": updated_bakery["name"],
        "wc_url": updated_bakery.get("wc_url"),
        "has_keys": bool(updated_bakery.get("wc_consumer_key") and updated_bakery.get("wc_consumer_secret"))
    }
