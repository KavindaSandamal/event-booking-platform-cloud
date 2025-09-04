from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class EventIn(BaseModel):
    title: str
    description: Optional[str]
    date: Optional[datetime]
    venue: Optional[str]
    capacity: int

class EventOut(EventIn):
    id: uuid.UUID
    created_at: datetime
