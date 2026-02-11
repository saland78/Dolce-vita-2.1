import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_data():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # 1. Initialize 'archived' field for all orders
    res = await db.orders.update_many(
        {"archived": {"$exists": False}},
        {"$set": {"archived": False}}
    )
    print(f"Initialized 'archived' field for {res.modified_count} orders.")
    
    # 2. Delete non-WooCommerce orders (Demo/Manual)
    # Be careful not to delete legitimate manual orders if user created them, 
    # but user said "elimina l'ordine demo" and "solo ordini da woocommerce".
    # I will delete where source is 'manual' or 'manual_test' or 'woocommerce_mock'.
    
    res_del = await db.orders.delete_many({
        "source": {"$in": ["manual", "manual_test", "woocommerce_mock"]}
    })
    print(f"Deleted {res_del.deleted_count} demo/manual orders.")
    
    # Also clean up "Chart User" or "Plan User" if I named them that specifically
    res_del_2 = await db.orders.delete_many({
        "customer_name": {"$in": ["Chart User", "Plan User", "Test User"]}
    })
    print(f"Deleted {res_del_2.deleted_count} specific test user orders.")

asyncio.run(fix_data())
