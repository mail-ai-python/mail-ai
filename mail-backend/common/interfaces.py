"""
Interfaces module for the Mail AI Backend application.

This module defines the abstract contracts (interfaces) for services that can
be implemented by different providers (e.g., Google, Outlook). It is central
to the Strategy Pattern and SOLID design of the application.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

# --- Data Access Interfaces ---

class IUserRepository(ABC):
    """Interface for user data access."""
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def create_or_update_user(self, user_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def update_user_status(self, email: str, is_active: bool, last_started_at: Optional[datetime] = None) -> None:
        pass

    @abstractmethod
    async def update_user_prompt(self, email: str, prompt: str) -> None:
        pass

class IEmailRepository(ABC):
    """Interface for email log data access."""
    @abstractmethod
    async def get_email_log_by_message_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def insert_email_logs(self, logs: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    async def get_user_logs(self, email: str, limit: int, direction: str) -> List[Dict[str, Any]]:
        pass

# --- Service Provider Interfaces ---

class IAuthService(ABC):
    """
    Interface for an authentication service provider.
    """
    @abstractmethod
    def get_auth_url(self, email_hint: Optional[str] = None) -> str:
        """Generates the provider-specific authentication URL."""
        pass

    @abstractmethod
    async def handle_callback(self, code: str) -> Dict[str, Any]:
        """
        Handles the OAuth callback and returns standardized user and token data.
        The returned dictionary should include 'email', 'refresh_token', etc.
        """
        pass

class IEmailProvider(ABC):
    """
    Interface for an email service provider.
    """
    @abstractmethod
    async def setup_watch(self, user_credentials: Dict[str, Any]) -> str:
        """
        Sets up push notifications/webhooks for new emails.
        Returns a status string.
        """
        pass

    @abstractmethod
    async def get_message(self, message_id: str, user_credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches a single email message by its ID and returns it in a
        standardized application format.
        """
        pass

    @abstractmethod
    async def get_latest_message_id(self, user_credentials: Dict[str, Any]) -> Optional[str]:
        """
        Fetches the ID of the most recent message in the user's inbox.
        """
        pass
