"""
Summarizer module for the Mail AI Backend application.

This module handles AI-powered summarization of emails using different
AI providers. It follows the Single Responsibility Principle by focusing
solely on summarization operations and uses the Strategy Pattern for
different AI services.
"""

from typing import Optional
from common.ai_factory import AIFactory
from common.interfaces import IAIService


class EmailSummarizer:
    """
    Service class for email summarization.

    Uses AI services to generate summaries of email content with context.
    """

    def __init__(self):
        """
        Initialize EmailSummarizer.

        Note: AI service is created per request to ensure up-to-date configuration.
        """
        pass

    async def summarize_email(self, context_str: str, email_content: str,
                            ai_provider: str, prompt_template: str) -> str:
        """
        Generate AI summary of an email with context.

        Args:
            context_str: Historical conversation context.
            email_content: Current email content to summarize.
            ai_provider: AI provider to use ('gemini', 'openai', etc.).
            prompt_template: Template for the AI prompt.

        Returns:
            AI-generated summary string.
        """
        try:
            # Get AI service instance
            ai_service = AIFactory.get_service(ai_provider)

            # Build full prompt
            full_prompt = self._build_prompt(prompt_template, context_str, email_content)

            # Generate summary
            summary = ai_service.summarize(full_prompt, "Context-Aware Email Summary")

            return summary

        except Exception as e:
            print(f"[Summarizer Error]: {e}")
            return f"AI Summarization Failed: {str(e)}"

    def _build_prompt(self, template: str, context: str, email_content: str) -> str:
        """
        Build the complete prompt from template and content.

        Args:
            template: Prompt template string.
            context: Conversation context.
            email_content: Email content.

        Returns:
            Complete prompt string.
        """
        try:
            return template.format(
                context=context or "No previous conversation history.",
                email_content=email_content
            )
        except KeyError as e:
            # Fallback if template has missing placeholders
            print(f"[Prompt Build Error]: {e}. Using fallback.")
            return f"Context: {context}\n\nEmail: {email_content}\n\nPlease summarize this email."
