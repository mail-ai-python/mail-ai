"""
Factory for creating integration instances.
"""

from integrations.interfaces import IAuthIntegration, IEventIntegration, IEmailProvider, IWebhookProcessor
from integrations.email.google.google_auth import GoogleAuth
from integrations.email.outlook.outlook_auth import OutlookAuth
from integrations.email.google.google_events import GoogleEventIntegration
from integrations.email.google.google_email import GoogleEmailProvider
from integrations.email.google.google_webhook import GoogleWebhookProcessor
from integrations.email.outlook.outlook_webhook import OutlookWebhookProcessor
from integrations.ai.factory import AIFactory

class IntegrationFactory:
    """
    Factory class for creating integration instances.
    """
    _auth_integrations = {"google": GoogleAuth, "outlook": OutlookAuth}
    _event_integrations = {"google": GoogleEventIntegration}
    _email_providers = {"google": GoogleEmailProvider}
    _webhook_processors = {"google": GoogleWebhookProcessor, "outlook": OutlookWebhookProcessor, "gmail": GoogleWebhookProcessor}

    @staticmethod
    def get_auth_integration(provider: str) -> IAuthIntegration:
        integration_class = IntegrationFactory._auth_integrations.get(provider)
        if not integration_class: raise ValueError(f"Unsupported auth provider: {provider}")
        return integration_class()

    @staticmethod
    def get_event_integration(provider: str) -> IEventIntegration:
        integration_class = IntegrationFactory._event_integrations.get(provider)
        if not integration_class: raise ValueError(f"Unsupported event provider: {provider}")
        return integration_class()

    @staticmethod
    def get_email_provider(provider: str) -> IEmailProvider:
        provider_class = IntegrationFactory._email_providers.get(provider)
        if not provider_class: raise ValueError(f"Unsupported email provider: {provider}")
        return provider_class()

    @staticmethod
    def get_webhook_processor(provider: str) -> IWebhookProcessor:
        processor_class = IntegrationFactory._webhook_processors.get(provider)
        if not processor_class: raise ValueError(f"Unsupported webhook provider: {provider}")
        return processor_class()

    @staticmethod
    def get_ai_service(provider: str):
        return AIFactory.get_service(provider)
