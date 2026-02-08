"""
Google-specific event integration using Pub/Sub.
"""

import os
import json
import asyncio
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from integrations.interfaces import IEventIntegration
from core.config import settings

class GoogleEventIntegration(IEventIntegration):
    """
    Google implementation of the IEventIntegration interface.
    """

    def __init__(self):
        service_account_info = json.loads(settings.google_service_account_json)
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        self.subscriber = pubsub_v1.SubscriberClient(credentials=creds)
        self.subscription_path = f"projects/{settings.project_id}/subscriptions/{settings.gmail_subscription_id}"
        self.future = None

    def start(self, callback):
        self.future = self.subscriber.subscribe(self.subscription_path, callback=callback)
        print(f"Listening on subscription: {self.subscription_path}...")

    def stop(self):
        if self.future:
            self.future.cancel()
        self.subscriber.close()
