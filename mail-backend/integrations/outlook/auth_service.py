"""
Outlook/Microsoft-specific implementation of the IAuthService interface.
"""
import os
from typing import Optional, Dict, Any
from msal import ConfidentialClientApplication
from common.interfaces import IAuthService

class OutlookAuthService(IAuthService):
    def __init__(self):
        self._client_id = os.getenv("OUTLOOK_CLIENT_ID")
        self._client_secret = os.getenv("OUTLOOK_CLIENT_SECRET")
        self._authority = "https://login.microsoftonline.com/common"
        self._redirect_uri = os.getenv("OUTLOOK_REDIRECT_URI")
        self._scopes = ["https://graph.microsoft.com/.default"]

        self._app = ConfidentialClientApplication(
            client_id=self._client_id,
            authority=self._authority,
            client_credential=self._client_secret
        )

    def get_auth_url(self, email_hint: Optional[str] = None) -> str:
        """Generates the Microsoft identity platform authorization URL."""
        auth_url = self._app.get_authorization_request_url(
            scopes=self._scopes,
            redirect_uri=self._redirect_uri,
            login_hint=email_hint or ""
        )
        return auth_url

    async def handle_callback(self, code: str) -> Dict[str, Any]:
        """Handles the OAuth callback from Microsoft."""
        result = self._app.acquire_token_by_authorization_code(
            code,
            scopes=self._scopes,
            redirect_uri=self._redirect_uri
        )

        if "error" in result:
            raise Exception(f"OAuth Error: {result.get('error_description')}")

        # In a real scenario, you would use the access token to get user info
        # from the Microsoft Graph API.
        # For now, we'll use a placeholder.
        # from services.graph_service import get_user_info
        # user_info = await get_user_info(result['access_token'])
        # email = user_info.get('mail') or user_info.get('userPrincipalName')

        # Placeholder email until Graph call is implemented
        email = "placeholder@outlook.com"

        return {
            "email": email,
            "provider": "outlook",
            "refresh_token": result.get("refresh_token"),
            "raw_credentials": result # Store the full token dictionary
        }
