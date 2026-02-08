import os
import sys
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add root directory to python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

from common.database import db
from common.user_repository import MongoUserRepository
from common.email_repository import MongoEmailRepository
from common.interfaces import IUserRepository, IEmailRepository
from core.config import settings
from integrations.factory import IntegrationFactory

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

class UserCheckRequest(BaseModel):
    email: str

class UpdatePromptRequest(BaseModel):
    email: str
    prompt: str

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
        raise HTTPException(status_code=404, detail="User not found")

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

@app.get("/login/{provider}")
def login(provider: str, email_hint: Optional[str] = None):
    try:
        auth_integration = IntegrationFactory.get_auth_integration(provider)
        redirect_uri = f"{settings.redirect_uri}/{provider}"
        auth_url = auth_integration.get_auth_url(redirect_uri, email_hint)
        return {"auth_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/callback/{provider}")
async def callback(provider: str, code: str, user_repo: IUserRepository = Depends(get_user_repo)):
    try:
        auth_integration = IntegrationFactory.get_auth_integration(provider)
        redirect_uri = f"{settings.redirect_uri}/{provider}"
        user_info = await auth_integration.handle_callback(code, redirect_uri)

        user_data = {
            "email": user_info["email"],
            "refresh_token": user_info["refresh_token"],
            "watch_status": user_info["watch_status"],
            "provider": provider,
        }

        existing_user = await user_repo.get_user_by_email(user_info["email"])
        if not existing_user:
            user_data["created_at"] = datetime.utcnow()
            user_data["is_active"] = False

        await user_repo.create_or_update_user(user_data)

        return RedirectResponse(f"{settings.frontend_url}/success?email={user_info['email']}&status={user_info['watch_status']}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
