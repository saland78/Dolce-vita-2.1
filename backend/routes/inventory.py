from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from models import Ingredient, Product
from database import get_db

router = APIRouter(prefix="/inventory", tags=["inventory"])

# --- Ingredients (Materie Prime) ---
@router.get("/ingredients", response_model=List[Ingredient])
async def get_ingredients(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await db.ingredients.find({}, {"_id": 0}).to_list(100)

@router.post("/ingredients", response_model=Ingredient)
async def create_ingredient(ing: Ingredient, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db.ingredients.insert_one(ing.model_dump(by_alias=True))
    return ing

# --- Products (Prodotti Finiti) ---
@router.get("/products", response_model=List[Product])
async def get_products(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await db.products.find({}, {"_id": 0}).to_list(100)

@router.post("/products", response_model=Product)
async def create_product(prod: Product, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db.products.insert_one(prod.model_dump(by_alias=True))
    return prod

@router.get("/products/{product_id}/orders")
async def get_product_orders(product_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Returns list of customers who ordered this product.
    Matching: items.product_id (string) == product_id (string)
    """
    pipeline = [
        {"$unwind": "$items"},
        {"$match": {"items.product_id": product_id}},
        {"$project": {
            "customer_name": 1,
            "customer_email": 1,
            "quantity": "$items.quantity",
            "created_at": 1,
            "_id": 0
        }},
        {"$sort": {"created_at": -1}}
    ]
    
    results = await db.orders.aggregate(pipeline).to_list(100)
    
    # Format dates
    for r in results:
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
            
    return results

@router.post("/seed")
async def seed_inventory(db: AsyncIOMotorDatabase = Depends(get_db)):
    if await db.ingredients.count_documents({}) > 0:
        return {"message": "Already seeded"}
        
    ingredients = [
        Ingredient(name="Farina 00", quantity=50, unit="kg", reorder_threshold=10, cost_per_unit=1.2),
        Ingredient(name="Zucchero Semolato", quantity=20, unit="kg", reorder_threshold=5, cost_per_unit=1.5),
        Ingredient(name="Cioccolato Fondente", quantity=10, unit="kg", reorder_threshold=2, cost_per_unit=12.0),
        Ingredient(name="Burro", quantity=15, unit="kg", reorder_threshold=3, cost_per_unit=8.0),
        Ingredient(name="Uova", quantity=200, unit="pz", reorder_threshold=30, cost_per_unit=0.3),
    ]
    
    for i in ingredients:
        await db.ingredients.insert_one(i.model_dump(by_alias=True))
        
    return {"message": "Seeded successfully"}
