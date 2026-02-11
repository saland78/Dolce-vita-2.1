import asyncio
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load env for migration
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def migrate():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # 1. Check if ANY user exists
    user = await db.users.find_one({})
    if not user:
        print("No users found. Creating Default Admin User...")
        # Create default user if none
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": "admin@example.com",
            "name": "Admin User",
            "role": "admin",
            "created_at": datetime.now()
        }
        await db.users.insert_one(user)
    
    # 2. Check if ANY bakery exists
    bakery = await db.bakeries.find_one({})
    if not bakery:
        print("Creating Default Bakery from .env...")
        bakery = {
            "name": "Pasticceria Principale",
            "owner_user_id": user["user_id"],
            "wc_url": os.environ.get("WC_URL"),
            "wc_consumer_key": os.environ.get("WC_CONSUMER_KEY"),
            "wc_consumer_secret": os.environ.get("WC_CONSUMER_SECRET"),
            "created_at": datetime.now()
        }
        res = await db.bakeries.insert_one(bakery)
        bakery_id = str(res.inserted_id)
        
        # Link user
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"bakery_id": bakery_id}})
        print(f"Created Bakery {bakery_id} and linked to User.")
        
        # 3. Migrate DATA
        print("Migrating existing data to this Bakery...")
        # Add bakery_id to all existing records that miss it
        await db.orders.update_many({"bakery_id": {"$exists": False}}, {"$set": {"bakery_id": bakery_id}})
        await db.products.update_many({"bakery_id": {"$exists": False}}, {"$set": {"bakery_id": bakery_id}})
        await db.ingredients.update_many({"bakery_id": {"$exists": False}}, {"$set": {"bakery_id": bakery_id}})
        await db.customers.update_many({"bakery_id": {"$exists": False}}, {"$set": {"bakery_id": bakery_id}})
        
        # 4. Migrate Product IDs to Composite IDs (bakery_id + wc_id)
        # This is tricky. If we change _id, we break links in orders.
        # But we must do it for Multi-Tenant future proofing.
        # For THIS migration, we assume only 1 tenant exists so far.
        # We will iterate products, rename _id, and update orders items.product_id
        
        print("Migrating IDs to Composite Format...")
        products = await db.products.find({}).to_list(1000)
        for p in products:
            old_id = str(p["_id"])
            if "_" in old_id: continue # Already migrated?
            
            new_id = f"{bakery_id}_{old_id}"
            
            # Insert copy with new ID
            p["_id"] = new_id
            p["bakery_id"] = bakery_id
            try:
                await db.products.insert_one(p)
                # Delete old
                await db.products.delete_one({"_id": old_id})
                
                # Update Orders referring to this product
                # items.product_id matches old_id
                await db.orders.update_many(
                    {"items.product_id": old_id},
                    {"$set": {"items.$.product_id": new_id}}
                )
            except Exception as e:
                print(f"Error migrating product {old_id}: {e}")
                
        # Also migrate Order IDs?
        # Ideally yes, but changing Order IDs breaks archived references if stored externally?
        # Let's do it for consistency.
        orders = await db.orders.find({}).to_list(1000)
        for o in orders:
            old_id = str(o["_id"])
            if "_" in old_id: continue
            
            new_id = f"{bakery_id}_{old_id}"
            o["_id"] = new_id
            o["bakery_id"] = bakery_id
            try:
                await db.orders.insert_one(o)
                await db.orders.delete_one({"_id": old_id})
            except Exception as e:
                print(f"Error migrating order {old_id}: {e}")

from datetime import datetime
asyncio.run(migrate())
