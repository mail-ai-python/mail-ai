"""
Abstract interfaces for third-party integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, Tuple
from fastapi import Request

class IAuthIntegration(ABC):
    """Abstract interface for authentication integrations."""
    @abstractmethod
    def get_auth_url(self, redirect_uri: str, email_hint: Optional[str] = None) -> str:
        """Generate the OAuth authorization URL."""
        pass

    @abstractmethod
    async def handle_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle the OAuth callback and return user info and tokens."""
        pass

class IEventIntegration(ABC):
    """Abstract interface for event integrations."""
    @abstractmethod
    def start(self, callback: Callable):
        """Start listening for events."""
        pass

    @abstractmethod
    def stop(self):
        """Stop listening for events."""
        pass

class IEmailProvider(ABC):
    """Abstract interface for email providers."""
    @abstractmethod
    async def get_new_emails(self, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch new emails for a user."""
        pass

    @abstractmethod
    async def get_thread_history(self, user: Dict[str, Any], thread_id: str) -> List[Dict[str, Any]]:
        """Fetch the history of an email thread."""
        pass

class IAIService(ABC):
    """Abstract interface for AI summarization services."""
    @abstractmethod
    def summarize(self, text: str, prompt: str) -> str:
        """Generate summary of the given text."""
        pass

class IWebhookProcessor(ABC):
    """Abstract interface for processing incoming webhooks."""
    @abstractmethod
    async def process_webhook(self, request: Request) -> Optional[Tuple[str, str]]:
        """
        Process the webhook request and return a tuple of (email_address, history_id) or None.
        Should also handle any initial validation requests (like for Outlook).
        """
        pass
