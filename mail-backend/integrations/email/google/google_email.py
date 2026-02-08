"""
Google-specific implementation of the IEmailProvider interface.
"""

import asyncio
from typing import Dict, Any, List
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from integrations.interfaces import IEmailProvider
from core.config import settings

def _get_credentials_sync(user: Dict[str, Any]) -> Credentials:
    """Synchronous function to get credentials."""
    creds = Credentials(
        None,
        refresh_token=user['refresh_token'],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds

def _get_new_emails_sync(user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Synchronous function to fetch new emails."""
    creds = _get_credentials_sync(user)
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])

    # This part is still a loop of blocking calls, which is fine inside the executor
    return [service.users().messages().get(userId='me', id=m['id']).execute() for m in messages]

def _get_thread_history_sync(user: Dict[str, Any], thread_id: str) -> List[Dict[str, Any]]:
    """Synchronous function to fetch thread history."""
    creds = _get_credentials_sync(user)
    service = build('gmail', 'v1', credentials=creds)
    thread = service.users().threads().get(userId='me', id=thread_id).execute()
    return thread.get('messages', [])

class GoogleEmailProvider(IEmailProvider):
    """
    Google implementation of the IEmailProvider interface.
    This class acts as an async wrapper around the synchronous, blocking functions.
    """

    async def get_new_emails(self, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get_new_emails_sync, user)

    async def get_thread_history(self, user: Dict[str, Any], thread_id: str) -> List[Dict[str, Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get_thread_history_sync, user, thread_id)
