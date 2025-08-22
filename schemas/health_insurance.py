from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class HealthInsuranceBase(BaseModel):
    """Base Health Insurance schema"""
    cnpj: str = Field(..., min_length=18, max_length=18, description="CNPJ number")
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    trade_name: Optional[str] = Field(None, max_length=255, description="Trade name")
    ans_code: str = Field(..., min_length=1, max_length=20, description="ANS registration code")
    address: Optional[str] = Field(None, description="Company address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, min_length=2, max_length=2, description="State (UF)")
    zip_code: Optional[str] = Field(None, max_length=10, description="ZIP code")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    is_active: bool = Field(True, description="Active status")

    @field_validator('cnpj')
    @classmethod
    def validate_cnpj(cls, v):
        """Validate CNPJ format"""
        if not v.replace('.', '').replace('/', '').replace('-', '').isdigit():
            raise ValueError('CNPJ must contain only numbers, dots, slashes, and hyphens')
        return v

    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        """Validate Brazilian state abbreviation"""
        if v and v.upper() not in [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]:
            raise ValueError('Invalid Brazilian state abbreviation')
        return v.upper() if v else v

class HealthInsuranceCreate(HealthInsuranceBase):
    """Schema for creating a health insurance company"""
    pass

class HealthInsuranceUpdate(BaseModel):
    """Schema for updating a health insurance company"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class HealthInsuranceResponse(HealthInsuranceBase):
    """Schema for health insurance response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class HealthInsuranceList(BaseModel):
    """Schema for health insurance list response"""
    items: List[HealthInsuranceResponse]
    total: int
    page: int
    size: int
    pages: int

class ContractBase(BaseModel):
    """Base Contract schema"""
    health_insurance_id: int = Field(..., description="Health insurance company ID")
    provider_id: int = Field(..., description="Healthcare provider ID")
    contract_number: str = Field(..., min_length=1, max_length=50, description="Contract number")
    start_date: datetime = Field(..., description="Contract start date")
    end_date: Optional[datetime] = Field(None, description="Contract end date")
    is_active: bool = Field(True, description="Active status")

class ContractCreate(ContractBase):
    """Schema for creating a contract"""
    pass

class ContractUpdate(BaseModel):
    """Schema for updating a contract"""
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class ContractResponse(ContractBase):
    """Schema for contract response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    } 