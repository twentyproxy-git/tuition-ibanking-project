from pydantic import BaseModel, Field
from typing import Optional

class TuitionRequest(BaseModel):
    mssv: str = Field(..., description="MSSV of the student requesting tuition information")

class PaymentRequest(BaseModel):
    mssv: str = Field(..., description="MSSV of the student requesting payment")
    otp: str = Field(..., description="OTP for payment verification")