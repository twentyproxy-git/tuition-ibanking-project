from pydantic import BaseModel, Field
from typing import Optional

class EmailRequest(BaseModel):
    email: str = Field(..., description="Email address of the recipient")
    otp: str = Field(..., description="OTP to be sent to the recipient")