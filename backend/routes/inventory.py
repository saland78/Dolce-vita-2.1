from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from models import Ingredient, IngredientCreate, Product, ProductCreate
from database import get_db
from dependencies import get_current_user_and_bakery
from pydantic import BaseModel

router = APIRouter(prefix="/inventory", tags=["inventory"])

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    reorder_threshold: Optional[float] = None
    cost_per_unit: Optional[float] = None

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
    
    ing = Ingredient(
        bakery_id=bakery_id,
        **ing_in.model_dump()
    )
    
    await db.ingredients.insert_one(ing.model_dump(by_alias=True))
    return ing

@router.put("/ingredients/{ing_id}", response_model=Ingredient)
async def update_ingredient(
    ing_id: str,
    update: IngredientUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    # Filter update data to remove None values
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    result = await db.ingredients.find_one_and_update(
        {"_id": ing_id, "bakery_id": bakery_id},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Ingredient not found")
        
    return result

@router.delete("/ingredients/{ing_id}")
async def delete_ingredient(
    ing_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    result = await db.ingredients.delete_one({"_id": ing_id, "bakery_id": bakery_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return {"status": "deleted"}

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
