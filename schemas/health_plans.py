from pydantic import BaseModel, Field
from typing import Optional, List

class HealthPlanBase(BaseModel):
    """Base Health Plan schema"""
    name: str = Field(..., min_length=3, max_length=255, description="Health plan name")
    operator_code: str = Field(..., min_length=2, max_length=20, description="Operator code")
    registration_number: str = Field(..., min_length=5, max_length=50, description="Registration number")
    description: Optional[str] = Field(None, description="Health plan description")
    active: bool = Field(True, description="Whether the health plan is active")

class HealthPlanCreate(HealthPlanBase):
    """Schema for creating a health plan"""
    pass

class HealthPlanUpdate(BaseModel):
    """Schema for updating a health plan"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    operator_code: Optional[str] = Field(None, min_length=2, max_length=20)
    registration_number: Optional[str] = Field(None, min_length=5, max_length=50)
    description: Optional[str] = None
    active: Optional[bool] = None

class HealthPlanResponse(HealthPlanBase):
    """Schema for health plan response"""
    id: int
    created_at: str
    updated_at: str

    model_config = {
        "from_attributes": True
    }

class HealthPlanList(BaseModel):
    """Schema for health plan list response"""
    items: List[HealthPlanResponse]
    total: int
    page: int
    size: int
    pages: int