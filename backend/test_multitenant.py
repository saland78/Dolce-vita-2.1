import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
import datetime

async def test_multi_tenant():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("--- STARTING MULTI-TENANT SIMULATION ---")
    
    # 1. Create Bakery A
    bakery_a = {
        "name": "Pasticceria A",
        "owner_user_id": "user_a",
        "created_at": datetime.datetime.now()
    }
    res_a = await db.bakeries.insert_one(bakery_a)
    bid_a = str(res_a.inserted_id)
    print(f"Created Bakery A: {bid_a}")
    
    # 2. Create Bakery B
    bakery_b = {
        "name": "Pasticceria B",
        "owner_user_id": "user_b",
        "created_at": datetime.datetime.now()
    }
    res_b = await db.bakeries.insert_one(bakery_b)
    bid_b = str(res_b.inserted_id)
    print(f"Created Bakery B: {bid_b}")
    
    # 3. Insert Order for A
    await db.orders.insert_one({
        "bakery_id": bid_a,
        "customer_name": "Cliente di A",
        "total_amount": 100,
        "status": "delivered",
        "created_at": datetime.datetime.now()
    })
    print("Inserted Order for A")
    
    # 4. Insert Order for B
    await db.orders.insert_one({
        "bakery_id": bid_b,
        "customer_name": "Cliente di B",
        "total_amount": 200,
        "status": "delivered",
        "created_at": datetime.datetime.now()
    })
    print("Inserted Order for B")
    
    # 5. Query as User A (Simulate Logic)
    orders_a = await db.orders.find({"bakery_id": bid_a}).to_list(100)
    print(f"\nUser A sees {len(orders_a)} orders.")
    if len(orders_a) == 1 and orders_a[0]["customer_name"] == "Cliente di A":
        print("✅ SUCCESS: User A sees ONLY their order.")
    else:
        print("❌ FAILURE: User A sees wrong data.")
        
    # 6. Query as User B
    orders_b = await db.orders.find({"bakery_id": bid_b}).to_list(100)
    print(f"User B sees {len(orders_b)} orders.")
    if len(orders_b) == 1 and orders_b[0]["customer_name"] == "Cliente di B":
        print("✅ SUCCESS: User B sees ONLY their order.")
    else:
        print("❌ FAILURE: User B sees wrong data.")

    # Cleanup
    await db.bakeries.delete_one({"_id": res_a.inserted_id})
    await db.bakeries.delete_one({"_id": res_b.inserted_id})
    await db.orders.delete_many({"bakery_id": {"$in": [bid_a, bid_b]}})

asyncio.run(test_multi_tenant())
