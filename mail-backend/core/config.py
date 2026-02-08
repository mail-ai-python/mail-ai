"""
Configuration module for the Mail AI Backend application.

This module centralizes all configuration settings, including environment variables,
CORS settings, and other app-wide configurations. It follows the Single Responsibility
Principle by handling only configuration concerns.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses Pydantic for validation and type conversion.
    """
    # Database settings
    mongo_url: str = "mongodb://localhost:27017"
    db_name: str = "mail_ai_db"

    # Google OAuth settings
    google_client_id: str
    google_client_secret: str
    project_id: str

    # AI Provider settings
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # App settings
    redirect_uri: str = "http://localhost:8000/callback"
    context_aware_prompt: str = """
    You are a helpful assistant.

    PREVIOUS CONTEXT:
    {context}

    NEW EMAIL:
    {email_content}

    TASK:
    Summarize the new email. If it refers to the context, explain the connection.
    """

    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",  # For local development
        "https://your-frontend-url.netlify.app"  # <-- IMPORTANT: REPLACE THIS
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Extra fields from .env
    backend_port: Optional[str] = None
    frontend_url: Optional[str] = None
    gmail_topic_name: Optional[str] = None
    gmail_subscription_id: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    outlook_client_secret_id: Optional[str] = None
    outlook_client_secret_value: Optional[str] = None
    default_ai_provider: Optional[str] = None
    service_account_file: Optional[str] = None
    google_service_account_json: Optional[str] = None
    google_client_secrets_json: Optional[str] = None
    summary_prompt: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
