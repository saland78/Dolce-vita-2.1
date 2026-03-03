import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def fix_pickup_dates():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # Find orders without pickup_date
    query = {
        "pickup_date": None,
        "status": {"$in": ["received", "in_production"]}
    }
    
    count = 0
    async for order in db.orders.find(query):
        # Fallback to created_at date
        created_at = order.get("created_at")
        if created_at:
            # created_at is datetime object in Mongo
            if isinstance(created_at, str):
                # Should not happen given model, but safety check
                d = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                d = created_at
                
            new_date = d.strftime("%Y-%m-%d")
            
            await db.orders.update_one(
                {"_id": order["_id"]},
                {"$set": {"pickup_date": new_date, "pickup_time": "ASAP"}}
            )
            count += 1
            print(f"Updated order {order.get('wc_order_id', '???')} with date {new_date}")

    print(f"Fixed {count} orders.")

asyncio.run(fix_pickup_dates())
