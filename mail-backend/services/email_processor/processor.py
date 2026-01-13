"""
Email Processor module for the Mail AI Backend application.

This module orchestrates the email processing workflow, coordinating
validation, parsing, deduplication, context building, and summarization.
It follows the Single Responsibility Principle by acting as a coordinator
and uses dependency injection for loose coupling.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from common.interfaces import IEmailProcessor, IUserRepository, IEmailRepository
from common.models import EmailLog
from services.email_processor.email_validator import EmailValidator
from services.email_processor.email_parser import EmailParser
from services.email_processor.deduplicator import EmailDeduplicator
from services.email_processor.context_builder import ContextBuilder
from services.email_processor.summarizer import EmailSummarizer
from core.config import settings


class EmailProcessor(IEmailProcessor):
    """
    Main email processing orchestrator.

    Coordinates all steps of email processing: validation, parsing,
    deduplication, context building, AI summarization, and persistence.
    """

    def __init__(self, user_repository: IUserRepository, email_repository: IEmailRepository):
        """
        Initialize EmailProcessor with dependencies.

        Args:
            user_repository: Repository for user data access.
            email_repository: Repository for email data access.
        """
        self._user_repository = user_repository
        self._email_repository = email_repository

        # Initialize components
        self._validator = EmailValidator(user_repository, email_repository)
        self._parser = EmailParser()
        self._deduplicator = EmailDeduplicator()
        self._context_builder = ContextBuilder(email_repository)
        self._summarizer = EmailSummarizer()

    async def process_email_event(self, email_address: str, history_id: str) -> None:
        """
        Process an incoming email event.

        This is the main entry point that orchestrates the entire email
        processing workflow.

        Args:
            email_address: User's email address.
            history_id: Gmail history ID (not used in current implementation).
        """
        try:
            # Step 1: Validate user and get user data
            is_valid, user = await self._validator.validate_user_active(email_address)
            if not is_valid:
                print(f"[Skipped] User {email_address} is inactive or not found.")
                return

            # Step 2: Setup Gmail API credentials
            creds = self._setup_credentials(user['refresh_token'])
            service = build('gmail', 'v1', credentials=creds)

            # Step 3: Get latest message
            message_data = await self._get_latest_message(service)
            if not message_data:
                return

            msg_id, thread_id, email_time = message_data

            # Step 4: Validate email age
            is_recent = await self._validator.validate_email_age(email_time, user.get('last_started_at'))
            if not is_recent:
                print(f"[Skipped] Old email from {email_time}")
                return

            # Step 5: Check for duplicates
            is_duplicate = await self._validator.validate_not_duplicate(msg_id)
            if not is_duplicate:
                self._deduplicator.mark_processed(msg_id)
                return

            # Step 6: Parse email content
            email_info = await self._parser.parse_email(service, msg_id)
            if not email_info:
                return

            # Step 7: Validate draft exclusion
            is_valid_draft = await self._validator.validate_draft_exclusion(email_info['label_ids'])
            if not is_valid_draft:
                print(f"[Skipped] Draft message {msg_id}")
                return

            # Step 8: Build conversation context
            context_depth = user.get('settings', {}).get('context_depth', 10)
            context_str = await self._context_builder.build_context(
                thread_id, service, email_address, msg_id, context_depth
            )

            # Step 9: Generate AI summary
            ai_provider = user.get('settings', {}).get('ai_provider', 'gemini')
            summary = await self._summarizer.summarize_email(
                context_str, email_info['snippet'], ai_provider, settings.context_aware_prompt
            )

            # Step 10: Save to database
            await self._save_email_log(email_address, msg_id, thread_id, email_info, summary, ai_provider, email_time)

            # Step 11: Mark as processed
            self._deduplicator.mark_processed(msg_id)

            print(f"[Success] Processed email {msg_id} for {email_address}")

        except Exception as e:
            print(f"[Processor Error]: {e}")

    def _setup_credentials(self, refresh_token: str) -> Credentials:
        """
        Setup Gmail API credentials from refresh token.

        Args:
            refresh_token: User's OAuth refresh token.

        Returns:
            Google API credentials object.
        """
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret
        )

        if not creds.valid:
            creds.refresh(Request())

        return creds

    async def _get_latest_message(self, service) -> Optional[tuple]:
        """
        Get the latest message from user's inbox.

        Args:
            service: Gmail API service instance.

        Returns:
            Tuple of (message_id, thread_id, timestamp) or None.
        """
        results = service.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        if not messages:
            return None

        msg_id = messages[0]['id']
        thread_id = messages[0]['threadId']

        # Get message metadata
        msg_meta = service.users().messages().get(userId='me', id=msg_id, format='minimal').execute()
        internal_date = int(msg_meta['internalDate']) / 1000
        email_time = datetime.fromtimestamp(internal_date)

        return msg_id, thread_id, email_time

    async def _save_email_log(self, email_address: str, msg_id: str, thread_id: str,
                            email_info: Dict[str, Any], summary: str, ai_provider: str,
                            email_time: datetime) -> None:
        """
        Save processed email to database.

        Args:
            email_address: User's email.
            msg_id: Gmail message ID.
            thread_id: Gmail thread ID.
            email_info: Parsed email information.
            summary: AI-generated summary.
            ai_provider: AI provider used.
            email_time: Email timestamp.
        """
        direction = "outbound" if 'SENT' in email_info['label_ids'] else "inbound"

        log_entry = EmailLog(
            user_email=email_address,
            message_id=msg_id,
            thread_id=thread_id,
            sender=email_info['sender'],
            subject=email_info['subject'],
            summary=summary,
            ai_provider=ai_provider,
            timestamp=email_time,
            direction=direction
        )

        await self._email_repository.insert_email_logs([log_entry.dict()])
