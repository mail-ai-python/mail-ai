"""
Dependencies module for the Mail AI Backend application.

This module provides dependency injection setup and factory functions
for creating service instances with their required dependencies.
It follows the Dependency Inversion Principle by depending on abstractions.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from common.database import Database
from common.user_repository import MongoUserRepository
from common.email_repository import MongoEmailRepository
from services.auth.auth_service import GoogleAuthService
from services.auth.user_service import UserService
from services.email_processor.email_processor import EmailProcessor
from core.config import settings


class Dependencies:
    """
    Container for application dependencies.

    Provides factory methods for creating service instances with
    proper dependency injection.
    """

    def __init__(self):
        """
        Initialize Dependencies container.

        Sets up database connection and repositories.
        """
        # Initialize database
        self._db_client = Database()
        self._db_client.connect()
        self._database = self._db_client.get_db()

        # Initialize repositories
        self._user_repository = MongoUserRepository(self._database)
        self._email_repository = MongoEmailRepository(self._database)

    def get_user_service(self) -> UserService:
        """
        Create and return UserService instance.

        Returns:
            Configured UserService with dependencies injected.
        """
        return UserService(self._user_repository)

    def get_auth_service(self) -> GoogleAuthService:
        """
        Create and return GoogleAuthService instance.

        Returns:
            Configured GoogleAuthService instance.
        """
        return GoogleAuthService()

    def get_email_processor(self) -> EmailProcessor:
        """
        Create and return EmailProcessor instance.

        Returns:
            Configured EmailProcessor with dependencies injected.
        """
        return EmailProcessor(self._user_repository, self._email_repository)

    def close(self):
        """
        Clean up resources.

        Closes database connections.
        """
        if self._db_client:
            self._db_client.close()


# Global dependencies instance
dependencies = Dependencies()
