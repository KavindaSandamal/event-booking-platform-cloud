from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class RefreshToken(BaseModel):
    refresh_token: str
