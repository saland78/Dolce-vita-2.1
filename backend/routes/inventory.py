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
        
    products = [
        Product(id="p1", name="Torta Sacher", description="Classica torta viennese al cioccolato", price=35.0, category="Torte", image_url="https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&q=80&w=400"),
        Product(id="p2", name="Croissant Vuoto", description="Sfoglia burrosa e fragrante", price=1.5, category="Colazione", image_url="https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&q=80&w=400"),
        Product(id="p3", name="Bignè Crema", description="Pasta choux ripiena di crema pasticcera", price=1.8, category="Mignon", image_url="https://images.unsplash.com/photo-1559599525-27a94f6c483a?auto=format&fit=crop&q=80&w=400"),
    ]
    
    for p in products:
        try:
            await db.products.insert_one(p.model_dump(by_alias=True))
        except:
            pass # duplicate key ignore
        
    return {"message": "Seeded successfully"}
