from fastapi import APIRouter, HTTPException, Depends, Query, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from models import Recipe, RecipeIngredient
from database import get_db
from dependencies import get_current_user_and_bakery

router = APIRouter(prefix="/production", tags=["production"])

@router.get("/ingredients")
async def get_daily_ingredients(
    date: Optional[str] = None, # YYYY-MM-DD
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    # 1. Fetch Recipes for this bakery
    recipes_cursor = db.recipes.find({"bakery_id": bakery_id})
    recipes = {}
    async for r in recipes_cursor:
        recipes[r["product_id"]] = r # Map by Product ID (e.g. bakeryID_wcID)

    # 2. Fetch Orders for the day (or active orders if no date, or orders pickup date = date)
    # Strategy: Calculate ingredients for ALL active orders (Received/In Production)
    # regardless of date, OR filter by pickup_date if provided.
    
    match_query = {
        "bakery_id": bakery_id,
        "status": {"$in": ["received", "in_production"]},
        "archived": {"$ne": True}
    }
    
    if date:
        match_query["pickup_date"] = date # Filter by specific pickup date if needed
        
    orders = await db.orders.find(match_query).to_list(1000)
    
    totals = {} # { "Farina": {"qty": 1000, "unit": "g"} }
    
    for order in orders:
        for item in order.get("items", []):
            pid = item.get("product_id")
            qty = item.get("quantity", 0)
            
            # Check meta weight first (e.g. customized weight)
            # If meta['weight_kg'] exists, use that as total weight for the item line
            # Else use recipe base weight * qty
            
            recipe = recipes.get(pid)
            if not recipe:
                continue
                
            # Calculate total weight needed for this line item
            # Logic: Recipe ingredients are for 'base_weight_kg' (e.g. 1kg cake).
            # We need to scale ingredients based on actual item weight.
            
            item_weight_kg = item.get("meta", {}).get("weight_kg")
            
            scale_factor = 1.0
            if item_weight_kg:
                # If we have explicit weight (e.g. 1.5kg cake), scale factor = 1.5 / base(1.0)
                scale_factor = (item_weight_kg * qty) / recipe.get("base_weight_kg", 1.0)
            else:
                # Default: Just quantity count (assuming base weight)
                scale_factor = float(qty)

            for ing in recipe.get("ingredients", []):
                name = ing["name"]
                amount = ing["quantity_per_unit"] * scale_factor
                unit = ing["unit"]
                
                if name not in totals:
                    totals[name] = {"qty": 0.0, "unit": unit}
                
                totals[name]["qty"] += amount
                
    # Format list
    result = [{"name": k, "quantity": v["qty"], "unit": v["unit"]} for k, v in totals.items()]
    return result

@router.post("/recipes")
async def create_recipe(
    recipe: Recipe,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    recipe.bakery_id = bakery_id
    await db.recipes.insert_one(recipe.model_dump(by_alias=True))
    return recipe
