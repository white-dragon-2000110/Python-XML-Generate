from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal

class ClaimBase(BaseModel):
    """Base Claim schema"""
    patient_id: int = Field(..., description="Patient ID")
    provider_id: int = Field(..., description="Provider ID")
    plan_id: int = Field(..., description="Health plan ID")
    procedure_code: str = Field(..., min_length=3, max_length=20, description="Procedure code")
    diagnosis_code: str = Field(..., min_length=3, max_length=20, description="Diagnosis code")
    date: date = Field(..., description="Claim date")
    value: Decimal = Field(..., gt=0, description="Claim value")
    description: Optional[str] = Field(None, description="Claim description")
    status: str = Field("pending", description="Claim status")

class ClaimCreate(ClaimBase):
    """Schema for creating a claim"""
    pass

class ClaimResponse(ClaimBase):
    """Schema for claim response"""
    id: int
    created_at: str
    updated_at: str

    model_config = {
        "from_attributes": True
    } 