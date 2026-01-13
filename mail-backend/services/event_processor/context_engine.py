from datetime import datetime
from common.models import EmailLog
from common.interfaces import IEmailRepository

class ContextEngine:
    def __init__(self, email_repo: IEmailRepository):
        self.email_repo = email_repo

    async def get_thread_context(self, thread_id: str, gmail_service, user_email: str, current_message_id: str, limit: int = 10) -> str:
        if not thread_id: return ""

        existing_logs = await self.email_repo.get_thread_logs(thread_id, limit=100)
        
        if len(existing_logs) >= limit:
            return self._format_logs(existing_logs[-limit:])

        try:
            thread_data = gmail_service.users().threads().get(userId='me', id=thread_id).execute()
            messages = thread_data.get('messages', [])
            
            existing_ids = {log['message_id'] for log in existing_logs}
            new_logs_to_create = []

            for msg in messages:
                msg_id = msg['id']
                if msg_id == current_message_id or msg_id in existing_ids:
                    continue
                
                headers = msg['payload']['headers']
                sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                snippet = msg.get('snippet', '')
                internal_date = int(msg['internalDate']) / 1000
                timestamp = datetime.fromtimestamp(internal_date)

                log_entry = EmailLog(
                    user_email=user_email,
                    message_id=msg_id,
                    thread_id=thread_id,
                    sender=sender,
                    subject=subject,
                    summary=f"[Backfilled] {snippet}", 
                    ai_provider="system-backfill",
                    timestamp=timestamp
                )
                new_logs_to_create.append(log_entry)

            if new_logs_to_create:
                await self.email_repo.insert_email_logs([log.dict() for log in new_logs_to_create])
                existing_logs.extend([log.dict() for log in new_logs_to_create])
                existing_logs.sort(key=lambda x: x['timestamp'])

        except Exception as e:
            print(f"   [ContextEngine Error]: {e}")
        
        return self._format_logs(existing_logs[-limit:])

    def _format_logs(self, logs) -> str:
        history_text = [
            f"[{log['timestamp'].strftime('%Y-%m-%d %H:%M')}] {log['sender']} said: {log['summary']}"
            for log in logs
        ]
        return "\n".join(history_text) if history_text else "No previous context available."