import os
import sys
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorDatabase

# --- 1. LOAD ENV FIRST ---
load_dotenv()

# --- 2. IMPORTS ---
from common.database import db
from common.user_repository import MongoUserRepository
from common.email_repository import MongoEmailRepository
from common.interfaces import IUserRepository, IEmailRepository

# --- 3. CONFIGURATION ---
CLIENT_SECRETS_FILE = "services/auth_service/client_secret.json"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
PROJECT_ID = os.getenv("PROJECT_ID")
TOPIC_NAME = os.getenv("GMAIL_TOPIC_NAME", "gmail-events") # Default for safety
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000") # Default for safety

app = FastAPI()

# --- 4. MIDDLEWARE (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. DEPENDENCY INJECTION ---
def get_user_repo() -> IUserRepository:
    return MongoUserRepository(db.get_db())

def get_email_repo() -> IEmailRepository:
    return MongoEmailRepository(db.get_db())

@app.on_event("startup")
async def startup():
    db.connect()

@app.on_event("shutdown")
async def shutdown():
    db.close()

# --- 6. DATA MODELS ---
class UserCheckRequest(BaseModel):
    email: str

class UpdatePromptRequest(BaseModel):
    email: str
    prompt: str
# --- 7. API ENDPOINTS ---

@app.post("/api/check-user")
async def check_user(
    request: UserCheckRequest,
    user_repo: IUserRepository = Depends(get_user_repo)
):
    user = await user_repo.get_user_by_email(request.email)
    if user:
        return {
            "exists": True,
            "is_active": user.get("is_active", False),
            "custom_prompt": user.get("custom_prompt", ""),
            "redirect": "/dashboard"
        }
    return {"exists": False, "redirect": "/auth"}

@app.get("/api/logs/{email}")
async def get_user_logs(
    email: str,
    limit: int = 20,
    email_repo: IEmailRepository = Depends(get_email_repo)
):
    logs = await email_repo.get_user_logs(email, limit, direction="inbound")
    for doc in logs:
        doc['_id'] = str(doc['_id'])
    return logs

@app.post("/api/user/{email}/toggle")
async def toggle_status(
    email: str,
    user_repo: IUserRepository = Depends(get_user_repo)
):
    user = await user_repo.get_user_by_email(email)
    if not user:
        return {"error": "User not found"}

    new_status = not user.get("is_active", False)
    last_started = datetime.utcnow() if new_status else None
    
    await user_repo.update_user_status(email, new_status, last_started)
    
    return {"status": "success", "is_active": new_status}

@app.post("/api/user/prompt")
async def update_prompt(
    request: UpdatePromptRequest,
    user_repo: IUserRepository = Depends(get_user_repo)
):
    await user_repo.update_user_prompt(request.email, request.prompt)
    return {"status": "success", "message": "Prompt updated successfully."}

@app.get("/login")
def login(email_hint: Optional[str] = None):
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return {"error": "client_secret.json missing"}
        
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', login_hint=email_hint)
    return {"auth_url": auth_url}

@app.get("/callback")
async def callback(
    code: str,
    user_repo: IUserRepository = Depends(get_user_repo)
):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    service = build('oauth2', 'v2', credentials=creds)
    email = service.userinfo().get().execute()['email']

    try:
        gmail_service = build('gmail', 'v1', credentials=creds)
        request_body = {'labelIds': ['INBOX'], 'topicName': f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}"}
        gmail_service.users().watch(userId='me', body=request_body).execute()
        watch_status = "Active"
    except Exception as e:
        watch_status = f"Failed ({e})"

    user_data = {
        "email": email,
        "refresh_token": creds.refresh_token,
        "watch_status": watch_status
    }
    
    existing_user = await user_repo.get_user_by_email(email)
    if not existing_user:
        user_data["created_at"] = datetime.utcnow()
        user_data["is_active"] = False
    
    await user_repo.create_or_update_user(user_data)

    return RedirectResponse(f"{FRONTEND_URL}/success?email={email}&status={watch_status}")