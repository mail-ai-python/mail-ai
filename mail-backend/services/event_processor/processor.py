import os
import sys
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
            print(f"[Processor] Starting event for {email_address}")
            user = await self.user_repo.get_user_by_email(email_address)
            if not user or not user.get('is_active', False):
                if user: print(f"[Processor] User {email_address} is INACTIVE. Skipping.")
                else: print(f"[Processor] User {email_address} not found. Skipping.")
                return

            print("[Processor] Refreshing user credentials...")
            creds = Credentials(
                None, refresh_token=user['refresh_token'],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
            )
            if not creds.valid:
                creds.refresh(Request())
                print("[Processor] Credentials refreshed successfully.")

            service = build('gmail', 'v1', credentials=creds)

            results = service.users().messages().list(userId='me', maxResults=1).execute()
            if not results.get('messages', []):
                print("[Processor] No new messages found.")
                return
            
            msg_id = results['messages'][0]['id']
            thread_id = results['messages'][0]['threadId']
            print(f"[Processor] Found new message: ID {msg_id}")

            if self.history.is_seen(msg_id) or await self.email_repo.get_email_log_by_message_id(msg_id):
                print(f"[Processor] Message {msg_id} already processed. Skipping.")
                self.history.add(msg_id)
                return

            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            if 'DRAFT' in msg.get('labelIds', []):
                print(f"[Processor] Message {msg_id} is a draft. Skipping.")
                return

            internal_date = int(msg.get('internalDate', 0)) / 1000
            email_time = datetime.fromtimestamp(internal_date)

            last_started = user.get('last_started_at')
            if last_started and email_time < last_started:
                print(f"[Processor] Message {msg_id} is older than last start time. Skipping.")
                return

            direction = "outbound" if 'SENT' in msg.get('labelIds', []) else "inbound"
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            snippet = msg.get('snippet', '')

            print(f"[Processor] Getting context for thread {thread_id}...")
            user_depth = user.get('settings', {}).get('context_depth', 10)
            context_str = await self.context_engine.get_thread_context(
                thread_id=thread_id,
                gmail_service=service,
                user_email=email_address,
                current_message_id=msg_id,
                limit=user_depth
            )
        
#             final_prompt = self.prompt_builder.build(context_str=context_str, email_content=snippet)
            custom_prompt = user.get("custom_prompt")
            final_prompt = self.prompt_builder.build(
                context_str=context_str,
                email_content=snippet,
                custom_template=custom_prompt
            )

            print("[Processor] Generating AI summary...")
            summary = ""
            ai_provider = ""
            try:
                ai_provider = user.get('settings', {}).get('ai_provider', 'gemini')
                ai_service = AIFactory.get_service(ai_provider)
                summary = ai_service.summarize(final_prompt, "Context-Aware Summary")
                print("[Processor] AI summary generated successfully.")
            except Exception as e:
                summary = f"[AI ERROR]: Could not generate summary. Details: {e}"
                print(f"[Processor] {summary}", file=sys.stderr)

            log_entry = EmailLog(
                user_email=email_address, message_id=msg_id, thread_id=thread_id,
                sender=sender, subject=subject, summary=summary,
                ai_provider=ai_provider, timestamp=email_time, direction=direction
            )
            
            await self.email_repo.insert_email_logs([log_entry.dict()])
            self.history.add(msg_id)
            print(f"[Processor] SUCCESS: Saved log for message {msg_id} for user {email_address}")

        except Exception as e:
            import traceback
            print(f"[Processor] UNHANDLED ERROR in process_event for {email_address}: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
