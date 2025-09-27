from pydantic import BaseModel, Field
from typing import Optional

class TuitionRequest(BaseModel):
    mssv: str = Field(..., description="MSSV of the student requesting tuition information")

class TuitionUpdate(BaseModel):
    tuition_id: str = Field(..., description="ID of the tuition record to update")
    status: str = Field(..., description="New status of the tuition (e.g., 'paid', 'unpaid')")