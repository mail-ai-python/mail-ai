"""
Deduplicator module for the Mail AI Backend application.

This module handles deduplication of email messages using an in-memory cache.
It follows the Single Responsibility Principle by focusing solely on
preventing duplicate processing of emails.
"""

from collections import deque
from typing import Set


class EmailDeduplicator:
    """
    Service class for email deduplication.

    Uses an in-memory cache to track processed message IDs and prevent
    duplicate processing within the application session.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize EmailDeduplicator with cache.

        Args:
            max_size: Maximum number of message IDs to keep in cache.
        """
        self._seen_ids: Set[str] = set()
        self._recent_ids = deque(maxlen=max_size)

    def is_duplicate(self, message_id: str) -> bool:
        """
        Check if message ID has been seen before.

        Args:
            message_id: Gmail message ID.

        Returns:
            True if duplicate, False if new.
        """
        return message_id in self._seen_ids

    def mark_processed(self, message_id: str) -> None:
        """
        Mark message ID as processed.

        Args:
            message_id: Gmail message ID to mark.
        """
        self._seen_ids.add(message_id)
        self._recent_ids.append(message_id)

        # Clean up old entries if cache is full
        if len(self._seen_ids) > self._recent_ids.maxlen:
            # Remove oldest entries to maintain cache size
            while len(self._seen_ids) > self._recent_ids.maxlen:
                oldest = self._recent_ids.popleft()
                self._seen_ids.discard(oldest)

    def clear_cache(self) -> None:
        """
        Clear the deduplication cache.

        Useful for testing or memory management.
        """
        self._seen_ids.clear()
        self._recent_ids.clear()
