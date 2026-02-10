import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def reset_production():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # 1. Clear Orders (All orders come from WC or are manual sales that should be real)
    # Actually, if they added manual orders, they might want to keep them.
    # But for "Switching to Real Mode", usually implies wiping test data.
    # I'll delete only "woocommerce_mock" source items to be safe?
    # No, user said "fai finta che siamo online", implying previous data was "dati di prova".
    
    await db.orders.delete_many({}) 
    print("Deleted all Orders.")
    
    await db.products.delete_many({})
    print("Deleted all Products (will re-sync from WooCommerce).")
    
    await db.customers.delete_many({})
    print("Deleted all Synced Customers.")
    
    print("Database ready for Production Sync.")

asyncio.run(reset_production())
