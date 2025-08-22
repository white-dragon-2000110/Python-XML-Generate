from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class HealthInsurance(Base):
    """Health Insurance Company Model"""
    __tablename__ = "health_insurances"
    
    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(18), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    ans_code = Column(String(20), unique=True, nullable=False)
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contracts = relationship("Contract", back_populates="health_insurance")

class Contract(Base):
    """Contract between Health Insurance and Provider"""
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    health_insurance_id = Column(Integer, ForeignKey("health_insurances.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    contract_number = Column(String(50), unique=True, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    health_insurance = relationship("HealthInsurance", back_populates="contracts")
    provider = relationship("Provider", back_populates="contracts")

# Provider model is defined in models/providers.py to avoid conflicts
# This file only contains HealthInsurance and Contract models

class Professional(Base):
    """Healthcare Professional Model"""
    __tablename__ = "professionals"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False, index=True)
    crm_crm_cro = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    specialty = Column(String(100))
    specialty_code = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - Provider is defined in models/providers.py
    provider = relationship("Provider", back_populates="professionals")

# Note: Patient and Claim models are defined in their respective files
# models/patients.py and models/claims.py 