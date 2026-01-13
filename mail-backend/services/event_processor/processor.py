import os
import asyncio
from datetime import datetime
from collections import deque
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from common.models import EmailLog
from common.ai_factory import AIFactory
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
        try:
            user = await self.user_repo.get_user_by_email(email_address)
            if not user or not user.get('is_active', False):
                if user: print(f"[Ignored] User {email_address} is INACTIVE.")
                return

            creds = Credentials(
                None, refresh_token=user['refresh_token'],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
            )
            if not creds.valid: creds.refresh(Request())
            service = build('gmail', 'v1', credentials=creds)

            results = service.users().messages().list(userId='me', maxResults=1).execute()
            if not results.get('messages', []): return
            
            msg_id = results['messages'][0]['id']
            thread_id = results['messages'][0]['threadId']

            msg_meta = service.users().messages().get(userId='me', id=msg_id, format='minimal').execute()
            internal_date = int(msg_meta['internalDate']) / 1000
            email_time = datetime.fromtimestamp(internal_date)
            
            last_started = user.get('last_started_at')
            if last_started and email_time < last_started:
                print(f"[Skipping] Old email from {email_time}")
                return

            if self.history.is_seen(msg_id) or await self.email_repo.get_email_log_by_message_id(msg_id):
                self.history.add(msg_id)
                return

            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            if 'DRAFT' in msg.get('labelIds', []): return

            direction = "outbound" if 'SENT' in msg.get('labelIds', []) else "inbound"
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            snippet = msg.get('snippet', '')

            print(f"Processing Mail from: {sender} (Thread: {thread_id})")

            user_depth = user.get('settings', {}).get('context_depth', 10)
            context_str = await self.context_engine.get_thread_context(
                thread_id=thread_id,
                gmail_service=service,
                user_email=email_address,
                current_message_id=msg_id,
                limit=user_depth
            )
        
            final_prompt = self.prompt_builder.build(context_str=context_str, email_content=snippet)

            try:
                ai_provider = user.get('settings', {}).get('ai_provider', 'gemini')
                ai_service = AIFactory.get_service(ai_provider)
                summary = ai_service.summarize(final_prompt, "Context-Aware Summary")
            except Exception as e:
                summary = f"[AI ERROR]: {e}"

            log_entry = EmailLog(
                user_email=email_address, message_id=msg_id, thread_id=thread_id,
                sender=sender, subject=subject, summary=summary,
                ai_provider=ai_provider, timestamp=email_time, direction=direction
            )
            
            await self.email_repo.insert_email_logs([log_entry.dict()])
            self.history.add(msg_id)
            print(f"SUCCESS: Saved Context-Aware Summary for {email_address}")

        except Exception as e:
            print(f"PROCESSOR ERROR: {e}")