from pydantic import BaseModel, Field
from typing import Optional

class OTPRequest(BaseModel):
    user_id: str = Field(..., description="ID of the user to whom the OTP is sent")