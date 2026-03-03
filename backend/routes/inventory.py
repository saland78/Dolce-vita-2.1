from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from models import Ingredient, IngredientCreate, Product, ProductCreate
from database import get_db
from dependencies import get_current_user_and_bakery

router = APIRouter(prefix="/inventory", tags=["inventory"])

# --- Ingredients ---
@router.get("/ingredients", response_model=List[Ingredient])
async def get_ingredients(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    return await db.ingredients.find({"bakery_id": bakery_id}).to_list(100)

@router.post("/ingredients", response_model=Ingredient)
async def create_ingredient(
    ing_in: IngredientCreate, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    # Manually create full Ingredient with bakery_id
    ing = Ingredient(
        bakery_id=bakery_id,
        **ing_in.model_dump()
    )
    
    await db.ingredients.insert_one(ing.model_dump(by_alias=True))
    return ing

# --- Products ---
@router.get("/products", response_model=List[Product])
async def get_products(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    return await db.products.find({"bakery_id": bakery_id}).to_list(100)

@router.post("/products", response_model=Product)
async def create_product(
    prod_in: ProductCreate, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    prod = Product(
        bakery_id=bakery_id,
        **prod_in.model_dump()
    )
    
    await db.products.insert_one(prod.model_dump(by_alias=True))
    return prod

@router.get("/products/{product_id}/orders")
async def get_product_orders(
    product_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    pipeline = [
        {
            "$match": {
                "bakery_id": bakery_id
            }
        },
        {"$unwind": "$items"},
        {"$match": {"items.product_id": product_id}},
        {"$project": {
            "customer_name": 1,
            "customer_email": 1,
            "quantity": "$items.quantity",
            "created_at": 1,
            "status": 1,
            "_id": 0
        }},
        {"$sort": {"created_at": -1}}
    ]
    
    results = await db.orders.aggregate(pipeline).to_list(100)
    
    for r in results:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
            
    return results
