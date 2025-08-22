from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum

class ProviderTypeEnum(str, Enum):
    """Provider type enumeration"""
    hospital = "hospital"
    clinic = "clinic"
    laboratory = "laboratory"
    imaging_center = "imaging_center"
    specialist = "specialist"
    general_practitioner = "general_practitioner"
    pharmacy = "pharmacy"
    ambulance = "ambulance"
    other = "other"

class ProviderBase(BaseModel):
    """Base Provider schema"""
    name: str = Field(..., min_length=3, max_length=255, description="Provider name")
    cnpj: str = Field(..., description="CNPJ number in format XX.XXX.XXX/XXXX-XX")
    type: ProviderTypeEnum = Field(..., description="Provider type")
    address: str = Field(..., min_length=10, description="Provider address")
    contact: str = Field(..., min_length=5, description="Contact person name")
    phone: Optional[str] = Field(None, description="Provider phone number")
    email: Optional[str] = Field(None, description="Provider email address")
    website: Optional[str] = Field(None, description="Provider website URL")
    active: bool = Field(True, description="Whether the provider is active")

    @field_validator('cnpj')
    @classmethod
    def validate_cnpj_format(cls, v):
        """Validate CNPJ format"""
        import re
        if not re.match(r'^[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}$', v):
            raise ValueError('CNPJ must be in format XX.XXX.XXX/XXXX-XX')
        return v

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Validate email format if provided"""
        if v is not None:
            import re
            if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', v):
                raise ValueError('Invalid email format')
        return v

    @field_validator('website')
    @classmethod
    def validate_website_format(cls, v):
        """Validate website format if provided"""
        if v is not None:
            import re
            if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', v):
                raise ValueError('Invalid website format. Must start with http:// or https://')
        return v

class ProviderCreate(ProviderBase):
    """Schema for creating a provider"""
    pass

class ProviderUpdate(BaseModel):
    """Schema for updating a provider"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    cnpj: Optional[str] = Field(None)
    type: Optional[ProviderTypeEnum] = None
    address: Optional[str] = Field(None, min_length=10)
    contact: Optional[str] = Field(None, min_length=5)
    phone: Optional[str] = None
    email: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    active: Optional[bool] = None

    @field_validator('cnpj')
    @classmethod
    def validate_cnpj_format(cls, v):
        """Validate CNPJ format if provided"""
        if v is not None:
            import re
            if not re.match(r'^[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}$', v):
                raise ValueError('CNPJ must be in format XX.XXX.XXX/XXXX-XX')
        return v

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Validate email format if provided"""
        if v is not None:
            import re
            if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', v):
                raise ValueError('Invalid email format')
        return v

    @field_validator('website')
    @classmethod
    def validate_website_format(cls, v):
        """Validate website format if provided"""
        if v is not None:
            import re
            if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', v):
                raise ValueError('Invalid website format. Must start with http:// or https://')
        return v

class ProviderResponse(ProviderBase):
    """Schema for provider response"""
    id: int
    created_at: str
    updated_at: str

    model_config = {
        "from_attributes": True
    }

class ProviderList(BaseModel):
    """Schema for provider list response"""
    items: list[ProviderResponse]
    total: int
    page: int
    size: int
    pages: int 