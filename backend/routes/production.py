from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from models import Recipe, RecipeIngredient
from database import get_db
from dependencies import get_current_user_and_bakery

router = APIRouter(prefix="/production", tags=["production"])

@router.get("/ingredients")
async def get_daily_ingredients(
    date: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    recipes_cursor = db.recipes.find({"bakery_id": bakery_id})
    recipes = {}
    async for r in recipes_cursor:
        recipes[r["product_id"]] = r

    match_query = {
        "bakery_id": bakery_id,
        "status": {"$in": ["received", "in_production"]},
        "archived": {"$ne": True}
    }
    if date:
        match_query["pickup_date"] = date

    orders = await db.orders.find(match_query).to_list(1000)
    totals = {}

    for order in orders:
        for item in order.get("items", []):
            pid = item.get("product_id")
            qty = item.get("quantity", 0)
            recipe = recipes.get(pid)
            if not recipe:
                continue
            item_weight_kg = item.get("meta", {}).get("weight_kg")
            scale_factor = (item_weight_kg * qty) / recipe.get("base_weight_kg", 1.0) if item_weight_kg else float(qty)
            for ing in recipe.get("ingredients", []):
                name = ing["name"]
                amount = ing["quantity_per_unit"] * scale_factor
                unit = ing["unit"]
                if name not in totals:
                    totals[name] = {"qty": 0.0, "unit": unit}
                totals[name]["qty"] += amount

    return [{"name": k, "quantity": round(v["qty"], 3), "unit": v["unit"]} for k, v in totals.items()]


@router.get("/recipes")
async def get_recipes(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    recipes = await db.recipes.find({"bakery_id": bakery_id}, {"_id": 0}).to_list(200)
    return recipes


@router.post("/recipes")
async def upsert_recipe(
    recipe: Recipe,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    recipe.bakery_id = bakery_id
    recipe_dict = recipe.model_dump(by_alias=True)
    await db.recipes.update_one(
        {"bakery_id": bakery_id, "product_id": recipe.product_id},
        {"$set": recipe_dict},
        upsert=True
    )
    return recipe_dict
