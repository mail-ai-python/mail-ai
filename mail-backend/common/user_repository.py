"""
User Repository module for the Mail AI Backend application.

This module implements the IUserRepository interface for user data access.
It follows the Repository Pattern to abstract database operations and follows
the Single Responsibility Principle by handling only data access concerns.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from common.interfaces import IUserRepository


class MongoUserRepository(IUserRepository):
    """
    MongoDB implementation of IUserRepository.

    Handles all user-related database operations using MongoDB.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize MongoUserRepository with database connection.

        Args:
            db: MongoDB database instance.
        """
        self._db = db
        self._collection = db.users

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user by email address.

        Args:
            email: User's email address.

        Returns:
            User document as dictionary, or None if not found.
        """
        return await self._collection.find_one({"email": email})

    async def create_or_update_user(self, user_data: Dict[str, Any]) -> None:
        """
        Create or update user record.

        Args:
            user_data: User data to insert or update.
        """
        await self._collection.update_one(
            {"email": user_data["email"]},
            {"$set": user_data},
            upsert=True
        )

    async def update_user_status(self, email: str, is_active: bool, last_started_at: Optional[datetime] = None) -> None:
        """
        Update user's active status and optionally last started time.

        Args:
            email: User's email address.
            is_active: New active status.
            last_started_at: Timestamp when user was last activated.
        """
        update_data = {"is_active": is_active}
        if last_started_at:
            update_data["last_started_at"] = last_started_at

        await self._collection.update_one(
            {"email": email},
            {"$set": update_data}
        )
