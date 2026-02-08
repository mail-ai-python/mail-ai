"""
Google-specific authentication implementation.
"""

import os
import json
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from integrations.interfaces import IAuthIntegration
from core.config import settings

class GoogleAuth(IAuthIntegration):
    """
    Google implementation of the IAuthIntegration interface.
    """

    def __init__(self):
        client_secrets_str = os.getenv("GOOGLE_CLIENT_SECRETS_JSON")
        if not client_secrets_str:
            raise ValueError("GOOGLE_CLIENT_SECRETS_JSON environment variable not set")
        self._client_config = json.loads(client_secrets_str)
        self._scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'openid'
        ]

    def get_auth_url(self, redirect_uri: str, email_hint: Optional[str] = None) -> str:
        flow = Flow.from_client_config(
            self._client_config,
            scopes=self.get_scopes(),
            redirect_uri=redirect_uri
        )
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            login_hint=email_hint
        )
        return auth_url

    async def handle_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        flow = Flow.from_client_config(
            self._client_config,
            scopes=self.get_scopes(),
            redirect_uri=redirect_uri
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        oauth_service = build('oauth2', 'v2', credentials=creds)
        user_info = oauth_service.userinfo().get().execute()
        email = user_info['email']

        watch_status = await self._setup_gmail_watch(creds)

        return {
            "email": email,
            "refresh_token": creds.refresh_token,
            "watch_status": watch_status
        }

    def get_scopes(self) -> list[str]:
        return self._scopes

    async def _setup_gmail_watch(self, creds) -> str:
        try:
            gmail_service = build('gmail', 'v1', credentials=creds)
            request_body = {
                'labelIds': ['INBOX'],
                'topicName': f"projects/{settings.project_id}/topics/{settings.gmail_topic_name}"
            }
            gmail_service.users().watch(userId='me', body=request_body).execute()
            return "Active"
        except Exception as e:
            return f"Failed ({str(e)})"
