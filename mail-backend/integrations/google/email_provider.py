"""
Google-specific implementation of the IEmailProvider interface.
"""
import os
from typing import Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from common.interfaces import IEmailProvider

class GoogleEmailProvider(IEmailProvider):

    def _get_credentials(self, user_credentials: Dict[str, Any]) -> Credentials:
        """Helper to build Google credentials from stored user data."""
        # The raw_credentials stored during auth callback can be used to reconstruct
        # the credentials object for API calls.
        return Credentials.from_authorized_user_info(user_credentials)

    async def setup_watch(self, user_credentials: Dict[str, Any]) -> str:
        creds = self._get_credentials(user_credentials)
        gmail_service = build('gmail', 'v1', credentials=creds)

        project_id = os.getenv("PROJECT_ID")
        topic_name = os.getenv("GMAIL_TOPIC_NAME", "gmail-events")
        full_topic_name = f"projects/{project_id}/topics/{topic_name}"

        request_body = {'labelIds': ['INBOX'], 'topicName': full_topic_name}
        gmail_service.users().watch(userId='me', body=request_body).execute()
        return "Active"

    async def get_message(self, message_id: str, user_credentials: Dict[str, Any]) -> Dict[str, Any]:
        creds = self._get_credentials(user_credentials)
        service = build('gmail', 'v1', credentials=creds)

        msg = service.users().messages().get(userId='me', id=message_id).execute()

        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "No Subject")
        snippet = msg.get('snippet', '')

        # Standardized format
        return {
            "id": msg.get("id"),
            "thread_id": msg.get("threadId"),
            "snippet": snippet,
            "sender": sender,
            "subject": subject,
            "is_draft": 'DRAFT' in msg.get('labelIds', []),
            "is_sent": 'SENT' in msg.get('labelIds', []),
            "internal_date": int(msg.get('internalDate', 0)) / 1000
        }

    async def get_latest_message_id(self, user_credentials: Dict[str, Any]) -> Optional[str]:
        creds = self._get_credentials(user_credentials)
        service = build('gmail', 'v1', credentials=creds)

        results = service.users().messages().list(userId='me', maxResults=1).execute()
        if not results.get('messages', []):
            return None
        return results['messages'][0]['id']
