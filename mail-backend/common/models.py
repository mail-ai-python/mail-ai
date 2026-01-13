from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserSettings(BaseModel):
    ai_provider: str = "gemini"
    context_depth: int = 10  # How many past emails to include?

class User(BaseModel):
    email: str
    refresh_token: str
    settings: UserSettings = Field(default_factory=UserSettings)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmailLog(BaseModel):
    user_email: str
    message_id: str      # Unique Gmail ID (Primary Key logic)
    thread_id: str       # The "Context Key" (Groups A <-> B conversation)
    sender: str
    subject: str
    summary: str
    full_body: Optional[str] = None # Optional: Store full text if you want deeper context later
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    direction: str = "inbound"  # "inbound" or "outbound"
    # MongoDB Index Hint (Not code, but logical):
    # Create compound index: (thread_id, timestamp) for fast fetching