"""
Abstract interfaces for the Mail AI Backend application.

This module defines abstract base classes (interfaces) following the Interface Segregation
Principle. It allows for loose coupling and easy extension of functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IUserRepository(ABC):
    """
    Abstract interface for user data access.

    Defines methods for user-related database operations.
    """
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by email."""
        pass

    @abstractmethod
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> None:
        """Create or update user record."""
        pass

    @abstractmethod
    async def update_user_status(self, email: str, is_active: bool, last_started_at: Optional[datetime] = None) -> None:
        """Update user's active status."""
        pass


class IEmailRepository(ABC):
    """
    Abstract interface for email log data access.

    Defines methods for email log-related database operations.
    """
    @abstractmethod
    async def get_email_log_by_message_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve email log by message ID."""
        pass

    @abstractmethod
    async def insert_email_logs(self, logs: list) -> None:
        """Insert multiple email logs."""
        pass

    @abstractmethod
    async def get_thread_logs(self, thread_id: str, limit: int = 10) -> list:
        """Retrieve logs for a specific thread."""
        pass

    @abstractmethod
    async def get_user_logs(self, email: str, limit: int, direction: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve logs for a specific user."""
        pass


class IAuthService(ABC):
    """
    Abstract interface for authentication services.

    Defines methods for OAuth and authentication operations.
    """
    @abstractmethod
    def get_auth_url(self, email_hint: Optional[str] = None) -> str:
        """Generate OAuth authorization URL."""
        pass

    @abstractmethod
    async def handle_callback(self, code: str) -> Dict[str, Any]:
        """Handle OAuth callback and return user info."""
        pass


class IEmailProcessor(ABC):
    """
    Abstract interface for email processing.

    Defines the main processing method that can be extended for different email handling strategies.
    """
    @abstractmethod
    async def process_email_event(self, email_address: str, history_id: str) -> None:
        """Process an incoming email event."""
        pass


class IAIService(ABC):
    """
    Abstract interface for AI summarization services.

    Defines methods for AI-powered text summarization.
    """
    @abstractmethod
    def summarize(self, text: str, prompt: str) -> str:
        """Generate summary of the given text."""
        pass
