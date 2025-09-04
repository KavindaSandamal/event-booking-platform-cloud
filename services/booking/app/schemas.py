from pydantic import BaseModel
import uuid
from typing import Optional

class BookingRequest(BaseModel):
    event_id: uuid.UUID
    seats: int = 1

class BookingOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_id: uuid.UUID
    seats: int
    status: str
