from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "aptech_freelance")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# ✅ Add this function
def get_database():
    return db
