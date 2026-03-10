from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing import Optional
from database import get_db
from dependencies import get_current_user_and_bakery
from datetime import datetime, timezone

router = APIRouter(prefix="/settings", tags=["settings"])

class SmtpSettings(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = 587
    username: Optional[str] = None
    password: Optional[str] = None
    from_email: Optional[str] = None

class BakerySettingsUpdate(BaseModel):
    name: Optional[str] = None
    wc_url: Optional[str] = None
    wc_consumer_key: Optional[str] = None
    wc_consumer_secret: Optional[str] = None
    smtp_settings: Optional[SmtpSettings] = None

class BakerySettingsResponse(BaseModel):
    name: str
    wc_url: Optional[str]
    has_keys: bool
    smtp_configured: bool = False
    smtp_host: Optional[str] = None
    smtp_username: Optional[str] = None
    smtp_from_email: Optional[str] = None

@router.get("/", response_model=BakerySettingsResponse)
async def get_settings(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    bakery = await db.bakeries.find_one({"_id": bakery_id})
    if not bakery:
        raise HTTPException(status_code=404, detail="Bakery not found")
        
    smtp = bakery.get("smtp_settings") or {}
    return {
        "name": bakery["name"],
        "wc_url": bakery.get("wc_url"),
        "has_keys": bool(bakery.get("wc_consumer_key") and bakery.get("wc_consumer_secret")),
        "smtp_configured": bool(smtp.get("host") and smtp.get("username") and smtp.get("password")),
        "smtp_host": smtp.get("host"),
        "smtp_username": smtp.get("username"),
        "smtp_from_email": smtp.get("from_email"),
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
    if settings.smtp_settings:
        smtp_dict = settings.smtp_settings.model_dump(exclude_none=True)
        if smtp_dict:
            update_data["smtp_settings"] = smtp_dict
        
    await db.bakeries.update_one({"_id": bakery_id}, {"$set": update_data})
    
    # Return updated state
    updated_bakery = await db.bakeries.find_one({"_id": bakery_id})
    smtp = updated_bakery.get("smtp_settings") or {}
    return {
        "name": updated_bakery["name"],
        "wc_url": updated_bakery.get("wc_url"),
        "has_keys": bool(updated_bakery.get("wc_consumer_key") and updated_bakery.get("wc_consumer_secret")),
        "smtp_configured": bool(smtp.get("host") and smtp.get("username") and smtp.get("password")),
        "smtp_host": smtp.get("host"),
        "smtp_username": smtp.get("username"),
        "smtp_from_email": smtp.get("from_email"),
    }
