"""
Main API Router and Notification Webhook Receiver.

This service handles all incoming API requests, including authentication and
the universal webhook for real-time event notifications from all providers.
"""
import os
import sys
import json
import base64
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# --- Pre-emptive Imports & Config ---
load_dotenv()
from common.database import db
from common.user_repository import MongoUserRepository
from common.email_repository import MongoEmailRepository
from common.interfaces import IUserRepository, IEmailRepository
from integrations.google.auth_service import GoogleAuthService
from integrations.outlook.auth_service import OutlookAuthService
from services.event_processor.processor import EmailProcessor

# --- App Setup ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# --- Dependency Injection & Lifecycle ---
def get_user_repo() -> IUserRepository: return MongoUserRepository(db.get_db())
def get_email_repo() -> IEmailRepository: return MongoEmailRepository(db.get_db())
@app.on_event("startup")
async def startup(): db.connect()
@app.on_event("shutdown")
async def shutdown(): db.close()

# --- Data Models for API Requests ---
class UserCheckRequest(BaseModel):
    email: str
class UpdatePromptRequest(BaseModel):
    prompt: str

# --- Universal Webhook Notification Endpoint ---
@app.post("/api/notifications")
async def receive_notifications(
    request: Request,
    user_repo: IUserRepository = Depends(get_user_repo),
    email_repo: IEmailRepository = Depends(get_email_repo)
):
    """
    Universal webhook for receiving push notifications from all providers.
    This endpoint now includes detailed debugging.
    """
    print("\n--- [Webhook] Notification Received ---")
    try:
        # --- Raw Body and Headers Logging ---
        body = await request.body()
        print(f"[Webhook DEBUG] Raw Body: {body.decode('utf-8')}")
        print(f"[Webhook DEBUG] Headers: {dict(request.headers)}")

        payload = json.loads(body)

        # --- Google Pub/Sub Logic ---
        if "message" in payload and "data" in payload["message"]:
            provider = "google"
            # The 'data' field is Base64 encoded.
            decoded_data = base64.b64decode(payload["message"]["data"]).decode('utf-8')
            message_data = json.loads(decoded_data)
            email_address = message_data.get("emailAddress")

            print(f"[Webhook] Successfully parsed Google Pub/Sub message for: {email_address}")

            if email_address:
                processor = EmailProcessor(user_repo, email_repo)
                await processor.process_event(email_address, provider)

            # Acknowledge the message with a 204 No Content
            return Response(status_code=204)

        # --- Placeholder for Outlook Logic ---
        # if 'value' in payload and 'subscriptionId' in payload['value'][0]:
        #     ...

        print("[Webhook] Notification payload was not in a recognized format (Google or Outlook).")
        return Response(status_code=204) # Still acknowledge to prevent retries

    except Exception as e:
        import traceback
        print(f"[Webhook] CRITICAL ERROR processing notification: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        # Return a 2xx status code anyway, so the provider doesn't get stuck in a retry loop.
        return Response(status_code=200)


# --- Smart Login Router ---
@app.get("/login")
def login(email_hint: Optional[str] = None):
    if not email_hint:
        auth_service = GoogleAuthService()
        auth_url = auth_service.get_auth_url()
        return RedirectResponse(auth_url)

    domain = email_hint.split('@')[-1].lower()
    google_domains = ["gmail.com", "googlemail.com"]
    outlook_domains = ["outlook.com", "hotmail.com", "live.com", "msn.com"]

    if domain in google_domains:
        auth_service = GoogleAuthService()
        auth_url = auth_service.get_auth_url(email_hint)
        return RedirectResponse(auth_url)
    elif domain in outlook_domains:
        auth_service = OutlookAuthService()
        auth_url = auth_service.get_auth_url(email_hint)
        return RedirectResponse(auth_url)
    else:
        auth_service = GoogleAuthService()
        auth_url = auth_service.get_auth_url(email_hint)
        return RedirectResponse(auth_url)

# --- Provider-Specific Callbacks (Unchanged) ---
@app.get("/callback/google")
async def callback_google(code: str, user_repo: IUserRepository = Depends(get_user_repo)):
    auth_service = GoogleAuthService()
    user_data = await auth_service.handle_callback(code)
    await user_repo.create_or_update_user(user_data)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(f"{frontend_url}/success?email={user_data['email']}")

@app.get("/callback/outlook")
async def callback_outlook(code: str, user_repo: IUserRepository = Depends(get_user_repo)):
    auth_service = OutlookAuthService()
    user_data = await auth_service.handle_callback(code)
    await user_repo.create_or_update_user(user_data)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(f"{frontend_url}/success?email={user_data['email']}")

# --- Generic User API Endpoints ---
@app.post("/api/check-user")
async def check_user(
    request: UserCheckRequest,
    user_repo: IUserRepository = Depends(get_user_repo)
):
    user = await user_repo.get_user_by_email(request.email)
    if user:
        return { "exists": True, "is_active": user.get("is_active", False), "custom_prompt": user.get("settings", {}).get("custom_prompt", ""), "redirect": "/dashboard" }
    return {"exists": False, "redirect": "/auth"}

@app.get("/api/logs/{email}")
async def get_user_logs(
    email: str, limit: int = 20, email_repo: IEmailRepository = Depends(get_email_repo)
):
    logs = await email_repo.get_user_logs(email, limit, direction="inbound")
    for doc in logs: doc['_id'] = str(doc['_id'])
    return logs

@app.post("/api/user/{email}/toggle")
async def toggle_status(
    email: str, user_repo: IUserRepository = Depends(get_user_repo)
):
    user = await user_repo.get_user_by_email(email)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    new_status = not user.get("is_active", False)
    last_started = datetime.utcnow() if new_status else None
    await user_repo.update_user_status(email, new_status, last_started)
    return {"status": "success", "is_active": new_status}

@app.post("/api/user/{email}/prompt")
async def update_prompt(
    email: str, request: UpdatePromptRequest, user_repo: IUserRepository = Depends(get_user_repo)
):
    await user_repo.update_user_prompt(email, request.prompt)
    return {"status": "success", "message": "Prompt updated successfully."}

