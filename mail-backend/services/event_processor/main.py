import os
import sys
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Response
from dotenv import load_dotenv

# Add root directory to python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

from common.database import db
from common.user_repository import MongoUserRepository
from common.email_repository import MongoEmailRepository
from services.event_processor.processor import EmailProcessor
from integrations.factory import IntegrationFactory

app = FastAPI()

@app.on_event("startup")
async def startup():
    db.connect()

@app.on_event("shutdown")
async def shutdown():
    db.close()

async def process_email_task(email_address: str, history_id: str):
    """Wrapper function to run the email processor."""
    user_repo = MongoUserRepository(db.get_db())
    email_repo = MongoEmailRepository(db.get_db())
    processor = EmailProcessor(user_repo, email_repo)
    await processor.process_event(email_address, history_id)

@app.post("/webhook/{provider}")
async def webhook(provider: str, request: Request, background_tasks: BackgroundTasks):
    """
    Generic webhook endpoint that delegates processing to the correct provider.
    """
    try:
        webhook_processor = IntegrationFactory.get_webhook_processor(provider)
        result = await webhook_processor.process_webhook(request)

        # Handle special cases like Outlook's validation response
        if isinstance(result, Response):
            return result

        if result:
            email_address, history_id = result
            print(f"Webhook processed for {provider}: {email_address}")
            background_tasks.add_task(process_email_task, email_address, history_id)

        # Acknowledge the message to prevent retries
        return Response(status_code=204)

    except Exception as e:
        print(f"Error processing webhook for provider {provider}: {e}", file=sys.stderr)
        # Return a success status code even on error to prevent the provider from retrying a bad message.
        return Response(status_code=204)
