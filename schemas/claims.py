from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal

class ClaimBase(BaseModel):
    """Base Claim schema"""
    patient_id: int = Field(..., description="Patient ID")
    provider_id: int = Field(..., description="Provider ID")
    plan_id: int = Field(..., description="Health plan ID")
    procedure_code: Optional[str] = Field(None, min_length=3, max_length=20, description="Procedure code")
    diagnosis_code: Optional[str] = Field(None, min_length=3, max_length=20, description="Diagnosis code")
    claim_date: date = Field(..., description="Claim date")
    value: Decimal = Field(..., gt=0, description="Claim value")
    description: Optional[str] = Field(None, description="Claim description")
    status: str = Field("pending", description="Claim status")

class ClaimCreate(ClaimBase):
    """Schema for creating a claim"""
    pass

class ClaimUpdate(BaseModel):
    """Schema for updating a claim"""
    procedure_code: Optional[str] = Field(None, min_length=3, max_length=20)
    diagnosis_code: Optional[str] = Field(None, min_length=3, max_length=20)
    claim_date: Optional[date] = None
    value: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = None
    status: Optional[str] = None

class ClaimResponse(ClaimBase):
    """Schema for claim response"""
    id: int
    created_at: str
    updated_at: str

    model_config = {
        "from_attributes": True
    }

class ClaimList(BaseModel):
    """Schema for claim list response"""
    items: List[ClaimResponse]
    total: int
    page: int
    size: int
    pages: int

class ClaimFilter(BaseModel):
    """Schema for filtering claims"""
    patient_id: Optional[int] = None
    provider_id: Optional[int] = None
    plan_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")

class ClaimXMLResponse(BaseModel):
    """Schema for claim XML response"""
    claim_id: int
    xml_content: str
    filename: str
    generated_at: str 