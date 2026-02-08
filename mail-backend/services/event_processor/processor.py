import asyncio
from datetime import datetime
from collections import deque
from pymongo.errors import BulkWriteError
from common.models import EmailLog
from integrations.factory import IntegrationFactory
from common.interfaces import IUserRepository, IEmailRepository
from services.event_processor.context_engine import ContextEngine
from services.event_processor.prompt_builder import PromptBuilder

class LocalHistory:
    def __init__(self, max_size=1000):
        self._seen_ids = deque(maxlen=max_size)
    def is_seen(self, message_id): return message_id in self._seen_ids
    def add(self, message_id): self._seen_ids.append(message_id)

class EmailProcessor:
    def __init__(self, user_repo: IUserRepository, email_repo: IEmailRepository):
        self.user_repo = user_repo
        self.email_repo = email_repo
        self.history = LocalHistory()
        self.context_engine = ContextEngine(email_repo)
        self.prompt_builder = PromptBuilder()

    async def process_event(self, email_address, history_id):
        msg_id = None
        try:
            user = await self.user_repo.get_user_by_email(email_address)
            if not user or not user.get('is_active', False):
                return

            provider = user.get("provider", "google")
            email_provider = IntegrationFactory.get_email_provider(provider)
            
            # This now uses the generic interface
            new_emails = await email_provider.get_new_emails(user)

            for email_data in new_emails:
                msg_id = email_data['id']

                if self.history.is_seen(msg_id) or await self.email_repo.get_email_log_by_message_id(msg_id):
                    continue

                if 'DRAFT' in email_data.get('labelIds', []):
                    continue

                email_time = datetime.fromtimestamp(int(email_data.get('internalDate', 0)) / 1000)
                last_started = user.get('last_started_at')
                if last_started and email_time < last_started:
                    continue

                thread_id = email_data['threadId']
                context_str = await self.context_engine.get_thread_context(user, thread_id, msg_id)
            
                custom_prompt = user.get("custom_prompt")
                final_prompt = self.prompt_builder.build(
                    context_str=context_str,
                    email_content=email_data.get('snippet', ''),
                    custom_template=custom_prompt
                )

                ai_provider_name = user.get('settings', {}).get('ai_provider', 'gemini')
                ai_service = IntegrationFactory.get_ai_service(ai_provider_name)
                summary = ai_service.summarize(final_prompt, "Context-Aware Summary")

                log_entry = EmailLog(
                    user_email=email_address, message_id=msg_id, thread_id=thread_id,
                    sender=next((h['value'] for h in email_data['payload']['headers'] if h['name'] == 'From'), "Unknown"),
                    subject=next((h['value'] for h in email_data['payload']['headers'] if h['name'] == 'Subject'), "No Subject"),
                    summary=summary,
                    ai_provider=ai_provider_name,
                    timestamp=email_time,
                    direction="outbound" if 'SENT' in email_data.get('labelIds', []) else "inbound"
                )

                await self.email_repo.insert_email_logs([log_entry.dict()])
                self.history.add(msg_id)
                print(f"[Processor] SUCCESS: Saved log for message {msg_id}")

        except BulkWriteError:
            print(f"[Processor] Duplicate message {msg_id} handled by another process. Skipping.")
            if msg_id: self.history.add(msg_id)
        except Exception as e:
            import traceback
            print(f"[Processor] UNHANDLED ERROR in process_event for {email_address}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
