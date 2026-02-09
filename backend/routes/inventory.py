from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from models import Ingredient, Product
from database import get_db

router = APIRouter(prefix="/inventory", tags=["inventory"])

# --- Ingredients ---
@router.get("/ingredients", response_model=List[Ingredient])
async def get_ingredients(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await db.ingredients.find({}, {"_id": 0}).to_list(100)

@router.post("/ingredients", response_model=Ingredient)
async def create_ingredient(ing: Ingredient, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db.ingredients.insert_one(ing.model_dump(by_alias=True))
    return ing

@router.put("/ingredients/{ing_id}", response_model=Ingredient)
async def update_ingredient(ing_id: str, ing_update: dict, db: AsyncIOMotorDatabase = Depends(get_db)):
    # Removing _id from update if present to avoid immutability error
    if "_id" in ing_update:
        del ing_update["_id"]
        
    result = await db.ingredients.find_one_and_update(
        {"_id": ing_id},
        {"$set": ing_update},
        return_document=True
    )
    return result

# --- Products ---
@router.get("/products", response_model=List[Product])
async def get_products(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await db.products.find({}, {"_id": 0}).to_list(100)

@router.post("/products", response_model=Product)
async def create_product(prod: Product, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db.products.insert_one(prod.model_dump(by_alias=True))
    return prod

@router.post("/seed")
async def seed_inventory(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Seeds some basic ingredients and products"""
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
        Product(name="Torta Sacher", description="Classica torta viennese al cioccolato", price=35.0, category="Torte"),
        Product(name="Croissant Vuoto", description="Sfoglia burrosa e fragrante", price=1.5, category="Colazione"),
        Product(name="Bignè Crema", description="Pasta choux ripiena di crema pasticcera", price=1.8, category="Mignon"),
    ]
    
    for p in products:
        await db.products.insert_one(p.model_dump(by_alias=True))
        
    return {"message": "Seeded successfully"}
