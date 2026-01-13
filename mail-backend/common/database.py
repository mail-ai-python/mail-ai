import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "mail_ai_db")

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        print(f"Connected to MongoDB at {MONGO_URL}")

    def get_db(self):
        return self.client[DB_NAME]

    def close(self):
        self.client.close()

db = Database()