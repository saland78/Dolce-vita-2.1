import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load env vars explicitly here as well to ensure standalone imports work
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ.get('MONGO_URL', "mongodb://localhost:27017")
db_name = os.environ.get('DB_NAME', "bakery_db")

client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

def get_db():
    return db
