import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "mail_ai_db")

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        if self.client is None:
            self.client = AsyncIOMotorClient(MONGO_URL)
            print(f"Connected to MongoDB at {MONGO_URL}")

    def get_db(self):
        return self.client[DB_NAME]

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

db = Database()
