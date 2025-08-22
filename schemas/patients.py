from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date

class PatientBase(BaseModel):
    """Base Patient schema"""
    name: str = Field(..., min_length=2, max_length=255, description="Patient full name")
    cpf: str = Field(..., description="CPF number in format XXX.XXX.XXX-XX")
    birth_date: date = Field(..., description="Patient birth date")
    address: str = Field(..., min_length=10, description="Patient address")
    phone: str = Field(..., description="Patient phone number")
    email: str = Field(..., description="Patient email address")

    @field_validator('cpf')
    @classmethod
    def validate_cpf_format(cls, v):
        """Validate CPF format"""
        import re
        if not re.match(r'^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}$', v):
            raise ValueError('CPF must be in format XXX.XXX.XXX-XX')
        return v

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Validate email format"""
        import re
        if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v):
        """Validate birth date is not in the future"""
        from datetime import date
        if v > date.today():
            raise ValueError('Birth date cannot be in the future')
        return v

class PatientCreate(PatientBase):
    """Schema for creating a patient"""
    pass

class PatientUpdate(BaseModel):
    """Schema for updating a patient"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    cpf: Optional[str] = Field(None)
    birth_date: Optional[date] = None
    address: Optional[str] = Field(None, min_length=10)
    phone: Optional[str] = None
    email: Optional[str] = Field(None)

    @field_validator('cpf')
    @classmethod
    def validate_cpf_format(cls, v):
        """Validate CPF format if provided"""
        if v is not None:
            import re
            if not re.match(r'^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}$', v):
                raise ValueError('CPF must be in format XXX.XXX.XXX-XX')
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

class PatientResponse(PatientBase):
    """Schema for patient response"""
    id: int
    created_at: str
    updated_at: str

    model_config = {
        "from_attributes": True
    }

class PatientList(BaseModel):
    """Schema for patient list response"""
    items: list[PatientResponse]
    total: int
    page: int
    size: int
    pages: int 