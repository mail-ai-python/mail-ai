"""
Google-specific webhook processing.
"""
import json
import base64
from typing import Optional, Tuple
from fastapi import Request
from integrations.interfaces import IWebhookProcessor

class GoogleWebhookProcessor(IWebhookProcessor):
    async def process_webhook(self, request: Request) -> Optional[Tuple[str, str]]:
        """
        Processes a webhook from Google Cloud Pub/Sub.
        """
        body = await request.json()

        envelope = body.get('message')
        if not envelope or 'data' not in envelope:
            return None

        # Decode the base64-encoded message data
        data_bytes = base64.b64decode(envelope.get('data'))
        data = json.loads(data_bytes.decode('utf-8'))

        email_address = data.get('emailAddress')
        history_id = data.get('historyId')

        if email_address and history_id:
            return email_address, history_id

        return None
