from pydantic import BaseModel, Field, field_validator
import re

class WebhookPayload(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_msisdn: str = Field(..., alias="from")
    to_msisdn: str = Field(..., alias="to")
    ts: str
    text: str | None = Field(default=None, max_length=4096)

    @field_validator('from_msisdn', 'to_msisdn')
    def validate_e164(cls, v):
        if not re.match(r'^\+\d+$', v):
            raise ValueError('Must be E.164 format (e.g., +123456)')
        return v