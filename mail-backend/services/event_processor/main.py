import os
import json
import asyncio
import sys
from dotenv import load_dotenv

# --- 1. LOAD ENV FIRST ---
load_dotenv()

# --- 2. CONFIGURATION ---
PROJECT_ID = os.getenv("PROJECT_ID")
SERVICE_ACCOUNT_JSON_STR = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
# Use env variable for subscription ID, with a default
GMAIL_SUBSCRIPTION_ID = os.getenv("GMAIL_SUBSCRIPTION_ID", "gmail-events-sub")

if not PROJECT_ID:
    print("ERROR: PROJECT_ID is missing. Check .env", file=sys.stderr)
    sys.exit(1)
if not SERVICE_ACCOUNT_JSON_STR:
    print("ERROR: GOOGLE_SERVICE_ACCOUNT_JSON is missing. Check .env", file=sys.stderr)
    sys.exit(1)

# --- 3. IMPORTS ---
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from common.database import db
from common.user_repository import MongoUserRepository
from common.email_repository import MongoEmailRepository
from services.event_processor.processor import EmailProcessor

# Construct the full subscription path
SUB_NAME = f"projects/{PROJECT_ID}/subscriptions/{GMAIL_SUBSCRIPTION_ID}"
MAIN_LOOP = None
processor = None

def callback(message):
    # --- THIS IS THE NEW LOG ---
    print("[Pub/Sub Callback] Message received from Google Cloud.")
    try:
        data = json.loads(message.data.decode('utf-8'))
        email_address = data.get('emailAddress')
        history_id = data.get('historyId')
        
        print(f"[Event Received] For: {email_address}")
        
        if MAIN_LOOP and not MAIN_LOOP.is_closed() and processor:
            asyncio.run_coroutine_threadsafe(
                processor.process_event(email_address, history_id), 
                MAIN_LOOP
            )
    except Exception as e:
        print(f"Error in Pub/Sub callback: {e}", file=sys.stderr)
    finally:
        message.ack()

async def main():
    global MAIN_LOOP, processor
    MAIN_LOOP = asyncio.get_running_loop()
    
    db.connect()
    
    # --- Initialize Repositories and Processor ---
    user_repo = MongoUserRepository(db.get_db())
    email_repo = MongoEmailRepository(db.get_db())
    processor = EmailProcessor(user_repo, email_repo)

    # Load credentials directly from the environment variable string
    service_account_info = json.loads(SERVICE_ACCOUNT_JSON_STR)
    creds = service_account.Credentials.from_service_account_info(service_account_info)

    subscriber = pubsub_v1.SubscriberClient(credentials=creds)
    
    print(f"Listening on subscription: {SUB_NAME}...")
    
    future = subscriber.subscribe(SUB_NAME, callback=callback)
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Shutdown signal received...")
    finally:
        future.cancel()
        subscriber.close()
        db.close()
        print("Service shut down gracefully.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] User interrupted the process.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
