"""
Email Parser module for the Mail AI Backend application.

This module handles parsing of Gmail message data into structured format.
It follows the Single Responsibility Principle by focusing solely on
email content extraction and formatting.
"""

from typing import Optional, Dict, Any


class EmailParser:
    """
    Service class for parsing Gmail message data.

    Extracts relevant information from Gmail API responses into
    structured dictionaries for further processing.
    """

    def __init__(self):
        """
        Initialize EmailParser.

        No dependencies required for basic parsing operations.
        """
        pass

    async def parse_email(self, gmail_service, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Parse a Gmail message into structured data.

        Args:
            gmail_service: Authenticated Gmail API service instance.
            message_id: Gmail message ID to parse.

        Returns:
            Dictionary with parsed email data, or None if parsing fails.
        """
        try:
            # Fetch full message
            msg = gmail_service.users().messages().get(userId='me', id=message_id).execute()

            # Extract headers
            headers = msg['payload']['headers']
            subject = self._extract_header(headers, 'Subject', 'No Subject')
            sender = self._extract_header(headers, 'From', 'Unknown')
            snippet = msg.get('snippet', '')
            label_ids = msg.get('labelIds', [])

            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'snippet': snippet,
                'label_ids': label_ids,
                'headers': headers
            }

        except Exception as e:
            print(f"[Email Parser Error]: Failed to parse message {message_id}: {e}")
            return None

    def _extract_header(self, headers: list, header_name: str, default: str = '') -> str:
        """
        Extract a specific header value from Gmail headers.

        Args:
            headers: List of header dictionaries from Gmail API.
            header_name: Name of the header to extract.
            default: Default value if header not found.

        Returns:
            Header value string.
        """
        for header in headers:
            if header['name'].lower() == header_name.lower():
                return header['value']
        return default
