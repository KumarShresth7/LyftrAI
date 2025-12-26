from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re

Base = declarative_base()

class MessageDB(Base):
    __tablename__ = "messages"

    message_id = Column(String, primary_key=True)
    from_msisdn = Column(String, nullable=False, index=True)
    to_msisdn = Column(String, nullable=False)
    text = Column(String, nullable=True)
    ts = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class WebhookPayload(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_: str = Field(..., alias="from")
    to: str
    ts: datetime
    text: str = Field(None, max_length=4096)

    @field_validator('from_', 'to')
    def validate_e164(cls, v):
        if not re.match(r'^\+\d+$', v):
            raise ValueError('Must be in E.164 format (e.g. +919876543210)')
        return v

class MessageResponse(BaseModel):
    message_id: str
    from_: str = Field(..., alias="from")
    to: str
    ts: datetime
    text: str | None

class StatsResponse(BaseModel):
    total_messages: int
    senders_count: int
    messages_per_sender: list[dict]
    first_message_ts: datetime | None
    last_message_ts: datetime | None