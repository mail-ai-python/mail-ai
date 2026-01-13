"""
Authentication Service module for the Mail AI Backend application.

This module handles OAuth authentication with Google, including generating
auth URLs and processing OAuth callbacks. It follows the Single Responsibility
Principle by focusing solely on authentication operations.
"""

import os
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from common.interfaces import IAuthService
from core.config import settings


class GoogleAuthService(IAuthService):
    """
    Service class for Google OAuth authentication.

    Handles the OAuth flow for Gmail API access.
    """

    def __init__(self):
        """
        Initialize GoogleAuthService with OAuth configuration.
        """
        self._client_secrets_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "client_secret.json"
        )
        self._scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'openid'
        ]
        self._redirect_uri = settings.redirect_uri

    def get_auth_url(self, email_hint: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            email_hint: Optional email hint to pre-fill in Google's login form.

        Returns:
            Authorization URL string.

        Raises:
            FileNotFoundError: If client_secret.json is missing.
        """
        if not os.path.exists(self._client_secrets_file):
            raise FileNotFoundError("client_secret.json missing")

        flow = Flow.from_client_secrets_file(
            self._client_secrets_file,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri
        )

        auth_url, _ = flow.authorization_url(
            prompt='consent',
            login_hint=email_hint
        )
        return auth_url

    async def handle_callback(self, code: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and retrieve user information.

        Args:
            code: Authorization code from OAuth callback.

        Returns:
            Dict containing user email and watch status.
        """
        flow = Flow.from_client_secrets_file(
            self._client_secrets_file,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri
        )

        # Exchange code for credentials
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Get user email
        oauth_service = build('oauth2', 'v2', credentials=creds)
        user_info = oauth_service.userinfo().get().execute()
        email = user_info['email']

        # Setup Gmail watch
        watch_status = await self._setup_gmail_watch(creds)

        return {
            "email": email,
            "watch_status": watch_status,
            "refresh_token": creds.refresh_token
        }

    async def _setup_gmail_watch(self, creds) -> str:
        """
        Setup Gmail push notifications (watch).

        Args:
            creds: OAuth credentials.

        Returns:
            Status string indicating success or failure.
        """
        try:
            gmail_service = build('gmail', 'v1', credentials=creds)
            request_body = {
                'labelIds': ['INBOX'],
                'topicName': f"projects/{settings.project_id}/topics/gmail-events"
            }
            gmail_service.users().watch(userId='me', body=request_body).execute()
            return "Active"
        except Exception as e:
            return f"Failed ({str(e)})"
