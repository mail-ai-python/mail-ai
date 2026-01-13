"""
Email Validator module for the Mail AI Backend application.

This module handles validation logic for email processing, including user status checks,
email age validation, and deduplication. It follows the Single Responsibility Principle
by focusing solely on validation concerns.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from common.interfaces import IUserRepository, IEmailRepository


class EmailValidator:
    """
    Service class for email validation operations.

    Provides methods to validate if an email should be processed based on
    user status, email age, and duplication checks.
    """

    def __init__(self, user_repository: IUserRepository, email_repository: IEmailRepository):
        """
        Initialize EmailValidator with repositories.

        Args:
            user_repository: Repository for user data access.
            email_repository: Repository for email data access.
        """
        self._user_repository = user_repository
        self._email_repository = email_repository

    async def validate_user_active(self, email_address: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if user exists and is active.

        Args:
            email_address: User's email address.

        Returns:
            Tuple of (is_valid, user_data). Returns (False, None) if invalid.
        """
        user = await self._user_repository.get_user_by_email(email_address)
        if not user:
            return False, None

        if not user.get('is_active', False):
            return False, None

        return True, user

    async def validate_email_age(self, email_timestamp: datetime, user_last_started: Optional[datetime]) -> bool:
        """
        Check if email is newer than user's last activation time.

        Args:
            email_timestamp: Email's timestamp.
            user_last_started: User's last activation timestamp.

        Returns:
            True if email should be processed, False if too old.
        """
        if user_last_started and email_timestamp < user_last_started:
            return False
        return True

    async def validate_not_duplicate(self, message_id: str) -> bool:
        """
        Check if email message has already been processed.

        Args:
            message_id: Gmail message ID.

        Returns:
            True if not duplicate, False if already processed.
        """
        existing_log = await self._email_repository.get_email_log_by_message_id(message_id)
        return existing_log is None

    async def validate_draft_exclusion(self, label_ids: list) -> bool:
        """
        Check if email is a draft that should be excluded.

        Args:
            label_ids: Gmail label IDs.

        Returns:
            True if should process, False if draft.
        """
        return 'DRAFT' not in label_ids
