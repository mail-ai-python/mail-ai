"""
Generic Email Processor.

This module contains the core business logic for processing an email event,
regardless of its provider. It uses the IEmailProvider interface to fetch
message details, ensuring the processing logic is never duplicated.
"""
import os
import sys
from datetime import datetime
from common.models import EmailLog
from common.ai_factory import AIFactory
from common.interfaces import IUserRepository, IEmailRepository, IEmailProvider
from integrations.google.email_provider import GoogleEmailProvider
# from integrations.outlook.email_provider import OutlookEmailProvider # <-- To be added
from services.event_processor.context_engine import ContextEngine
from services.event_processor.prompt_builder import PromptBuilder

class ProviderFactory:
    """A simple factory to get the correct email provider implementation."""
    @staticmethod
    def get_provider(provider_name: str) -> IEmailProvider:
        if provider_name == "google":
            return GoogleEmailProvider()
        # elif provider_name == "outlook":
        #     return OutlookEmailProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

class EmailProcessor:
    def __init__(self, user_repo: IUserRepository, email_repo: IEmailRepository):
        self.user_repo = user_repo
        self.email_repo = email_repo
        self.context_engine = ContextEngine(email_repo)
        self.prompt_builder = PromptBuilder()

    async def process_event(self, email_address: str, provider_name: str):
        try:
            print(f"[Processor] Starting event for {email_address} via {provider_name}")
            user = await self.user_repo.get_user_by_email(email_address)
            if not user or not user.get('is_active', False):
                print(f"[Processor] User {email_address} is inactive or not found. Skipping.")
                return

            # Use the factory to get the right provider
            provider = ProviderFactory.get_provider(provider_name)

            # Get the latest message ID from the provider
            message_id = await provider.get_latest_message_id(user.get("raw_credentials"))
            if not message_id:
                print("[Processor] No new messages found.")
                return

            # Check if already processed
            if await self.email_repo.get_email_log_by_message_id(message_id):
                print(f"[Processor] Message {message_id} already processed. Skipping.")
                return

            # Get the standardized message object from the provider
            msg = await provider.get_message(message_id, user.get("raw_credentials"))

            if msg.get("is_draft"):
                print(f"[Processor] Message {message_id} is a draft. Skipping.")
                return

            # --- CENTRALIZED PROCESSING LOGIC (UNCHANGED) ---

            email_time = datetime.fromtimestamp(msg["internal_date"])
            last_started = user.get('last_started_at')
            if last_started and email_time < last_started:
                print(f"[Processor] Message {message_id} is older than last start time. Skipping.")
                return

            print(f"[Processor] Getting context for thread {msg['thread_id']}...")
            # Note: Context engine would also need to be made provider-agnostic if it fetches mail
            # For now, assuming it works on the standardized data in the DB.
            context_str = "Context logic would go here."

            custom_prompt = user.get("settings", {}).get("custom_prompt")
            final_prompt = self.prompt_builder.build(
                context_str=context_str,
                email_content=msg["snippet"],
                custom_template=custom_prompt
            )

            print("[Processor] Generating AI summary...")
            ai_provider_name = user.get('settings', {}).get('ai_provider', 'gemini')
            ai_service = AIFactory.get_service(ai_provider_name)
            summary = ai_service.summarize(final_prompt, "Context-Aware Summary")

            log_entry = EmailLog(
                user_email=email_address, message_id=msg["id"], thread_id=msg["thread_id"],
                sender=msg["sender"], subject=msg["subject"], summary=summary,
                ai_provider=ai_provider_name, timestamp=email_time,
                direction="outbound" if msg["is_sent"] else "inbound"
            )
            
            await self.email_repo.insert_email_logs([log_entry.dict()])
            print(f"[Processor] SUCCESS: Saved log for message {msg['id']}")

        except Exception as e:
            import traceback
            print(f"[Processor] UNHANDLED ERROR for {email_address}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
