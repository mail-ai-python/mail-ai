"""
Google-specific implementation of the IAuthService interface.
"""
import os
import json
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from common.interfaces import IAuthService

class GoogleAuthService(IAuthService):
    def __init__(self):
        secrets_str = os.getenv("GOOGLE_CLIENT_SECRETS_JSON")
        if not secrets_str:
            raise ValueError("GOOGLE_CLIENT_SECRETS_JSON environment variable not set")
        self._client_config = json.loads(secrets_str)
        self._scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'openid'
        ]
        self._redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

    def get_auth_url(self, email_hint: Optional[str] = None) -> str:
        flow = Flow.from_client_config(
            self._client_config, scopes=self._scopes, redirect_uri=self._redirect_uri
        )
        auth_url, _ = flow.authorization_url(prompt='consent', login_hint=email_hint)
        return auth_url

    async def handle_callback(self, code: str) -> Dict[str, Any]:
        flow = Flow.from_client_config(
            self._client_config, scopes=self._scopes, redirect_uri=self._redirect_uri
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()

        return {
            "email": user_info.get("email"),
            "provider": "google",
            "refresh_token": creds.refresh_token,
            "raw_credentials": json.loads(creds.to_json()) # Store the full credentials
        }
