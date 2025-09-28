from pydantic import BaseModel, Field
from typing import Optional

class OTPEmailRequest(BaseModel):
    email: str = Field(..., description="Email address of the recipient")
    otp: str = Field(..., description="OTP to be sent to the recipient")

class TransactionEmailRequest(BaseModel):
    email: str = Field(..., description="Email address of the recipient")
    debit: str = Field(..., description="Debit amount")
    content: str = Field(..., description="Content of the transaction")