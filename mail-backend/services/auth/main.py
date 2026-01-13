import sys
from typing import Optional, List
from datetime import datetime  # <--- FIXED: Added missing import
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv

# --- 1. SETUP & PATHS ---
# Add root directory to python path so we can import 'common'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

# Load Environment Variables
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Import from common (Must happen after sys.path.append)
from common.database import db
from common.models import User

# Configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(CURRENT_DIR, "client_secret.json")
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]
REDIRECT_URI = "http://localhost:8000/callback"
PROJECT_ID = os.getenv("PROJECT_ID")

app = FastAPI()

# --- 2. MIDDLEWARE (CORS) ---
# Critical for Frontend (Port 3000) to talk to Backend (Port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    db.connect()

# --- 3. DATA MODELS FOR API ---
class UserCheckRequest(BaseModel):
    email: str

class ToggleRequest(BaseModel):
    is_active: bool

# --- 4. DASHBOARD API ENDPOINTS ---

# A. Smart Check: Does this user exist?
@app.post("/api/check-user")
async def check_user(request: UserCheckRequest):
    user = await db.get_db().users.find_one({"email": request.email})
    if user:
        return {
            "exists": True, 
            "is_active": user.get("is_active", False),
            "redirect": "/dashboard"
        }
    else:
        return {
            "exists": False, 
            "redirect": "/auth"
        }

# B. Fetch Logs: Get history for a specific user
# B. Fetch Logs: Get history for a specific user
@app.get("/api/logs/{email}")
async def get_user_logs(email: str, limit: int = 20):
    logs = []
    
    # FILTER: Exclude 'system-backfill' so we only see AI summaries
    query = {
        "user_email": email,
        "ai_provider": {"$ne": "system-backfill"},
        "direction": "inbound"
    }
    
    # Sort by newest first
    cursor = db.get_db().email_logs.find(query).sort("timestamp", -1).limit(limit)
    
    async for doc in cursor:
        doc['_id'] = str(doc['_id'])
        logs.append(doc)
    return logs

# C. Toggle Status: Start/Stop the Agent
@app.post("/api/user/{email}/toggle")
async def toggle_status(email: str):
    user = await db.get_db().users.find_one({"email": email})
    if not user: return {"error": "User not found"}
    
    # Flip the status
    new_status = not user.get("is_active", False)
    update_data = {"is_active": new_status}
    
    # If turning ON, record the time (to ignore old emails)
    if new_status:
        update_data["last_started_at"] = datetime.utcnow()
        
    await db.get_db().users.update_one({"email": email}, {"$set": update_data})
    
    return {"status": "success", "is_active": new_status}

# --- 5. AUTH FLOW ENDPOINTS ---

@app.get("/login")
def login(email_hint: Optional[str] = None):
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return {"error": "client_secret.json missing"}
        
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    
    # login_hint pre-fills the email in Google's login box
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        login_hint=email_hint 
    )
    return {"auth_url": auth_url}

@app.get("/callback")
async def callback(code: str):
    # Exchange code for token
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Get User Email
    service = build('oauth2', 'v2', credentials=creds)
    email = service.userinfo().get().execute()['email']

    # Setup Watch (Pub/Sub)
    try:
        gmail_service = build('gmail', 'v1', credentials=creds)
        request_body = {'labelIds': ['INBOX'], 'topicName': f"projects/{PROJECT_ID}/topics/gmail-events"}
        gmail_service.users().watch(userId='me', body=request_body).execute()
        watch_status = "Active"
    except Exception as e:
        watch_status = f"Failed ({e})"

    # Save User (Upsert)
    # Note: We do NOT set is_active=True here. User must click "Start" on dashboard.
    user_data = {
        "email": email,
        "refresh_token": creds.refresh_token,
        "watch_status": watch_status
    }
    
    # Only set created_at if it's a new user
    existing_user = await db.get_db().users.find_one({"email": email})
    if not existing_user:
        user_data["created_at"] = datetime.utcnow()
        user_data["is_active"] = False # Default to Stopped
    
    await db.get_db().users.update_one({"email": email}, {"$set": user_data}, upsert=True)

    # Redirect to Frontend Success Page
    return RedirectResponse(f"http://localhost:3000/success?email={email}&status={watch_status}")
=======
"""
Main application module for the Auth Service in the Mail AI Backend.

This module sets up the FastAPI application for authentication and user management.
It follows the Single Responsibility Principle by handling only application
startup and configuration concerns.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add root directory to python path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Import dependencies
from common.database import db
from common.user_repository import MongoUserRepository
from services.auth.auth_service import GoogleAuthService
from services.auth.user_service import UserService
from services.auth.routes import AuthRouter
from core.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Mail AI Auth Service",
    description="Authentication and user management service for Mail AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Initialize dependencies
user_repository = MongoUserRepository(db.get_db())
auth_service = GoogleAuthService()
user_service = UserService(user_repository)
auth_router = AuthRouter(auth_service, user_service)

# Include routes
app.include_router(auth_router.router)

@app.on_event("startup")
async def startup():
    """Initialize database connection on startup."""
    db.connect()

@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown."""
    db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth"}
