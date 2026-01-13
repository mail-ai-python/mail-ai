"""
Email Repository module for the Mail AI Backend application.

This module implements the IEmailRepository interface for email log data access.
It follows the Repository Pattern to abstract database operations and follows
the Single Responsibility Principle by handling only email-related data access.
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from .interfaces import IEmailRepository


class MongoEmailRepository(IEmailRepository):
    """
    MongoDB implementation of IEmailRepository.

    Handles all email log-related database operations using MongoDB.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize MongoEmailRepository with database connection.

        Args:
            db: MongoDB database instance.
        """
        self._db = db
        self._collection = db.email_logs

    async def get_email_log_by_message_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve email log by Gmail message ID.

        Args:
            message_id: Gmail message ID.

        Returns:
            Email log document as dictionary, or None if not found.
        """
        return await self._collection.find_one({"message_id": message_id})

    async def insert_email_logs(self, logs: List[Dict[str, Any]]) -> None:
        """
        Insert multiple email log documents.

        Args:
            logs: List of email log dictionaries to insert.
        """
        if logs:
            await self._collection.insert_many(logs)

    async def get_thread_logs(self, thread_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve email logs for a specific thread, sorted by timestamp.

        Args:
            thread_id: Gmail thread ID.
            limit: Maximum number of logs to return.

        Returns:
            List of email log dictionaries for the thread.
        """
        cursor = self._collection.find({"thread_id": thread_id}).sort("timestamp", 1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_user_logs(self, email: str, limit: int, direction: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve logs for a specific user.

        Args:
            email: The user's email.
            limit: The maximum number of logs to return.
            direction: The direction of the emails to retrieve.

        Returns:
            A list of email log documents.
        """
        query = {
            "user_email": email,
            "ai_provider": {"$ne": "system-backfill"},
        }
        if direction:
            query["direction"] = direction

        cursor = self._collection.find(query).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
