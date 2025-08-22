from sqlalchemy import Column, Integer, String, Text, Index, CheckConstraint, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum
import re


class ProviderType(enum.Enum):
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    LABORATORY = "laboratory"
    IMAGING_CENTER = "imaging_center"
    SPECIALIST = "specialist"
    GENERAL_PRACTITIONER = "general_practitioner"
    PHARMACY = "pharmacy"
    AMBULANCE = "ambulance"
    OTHER = "other"


class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    cnpj = Column(String(18), nullable=False, unique=True, index=True)  # Format: XX.XXX.XXX/XXXX-XX
    type = Column(Enum(ProviderType), nullable=False, index=True)
    address = Column(Text, nullable=False)
    contact = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    website = Column(String(255), nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(String(26), default=func.now())
    updated_at = Column(String(26), default=func.now(), onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="provider", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="provider")
    professionals = relationship("Professional", back_populates="provider")
    
    # Indexes and Constraints
    __table_args__ = (
        Index('idx_providers_cnpj', 'cnpj'),
        Index('idx_providers_name', 'name'),
        Index('idx_providers_type', 'type'),
        Index('idx_providers_active', 'active'),
        Index('idx_providers_email', 'email'),
        Index('idx_providers_created_at', 'created_at'),
        
        # Composite indexes for common queries
        Index('idx_providers_type_active', 'type', 'active'),
        Index('idx_providers_name_type', 'name', 'type'),
        Index('idx_providers_cnpj_active', 'cnpj', 'active'),
        
        # Constraints
        CheckConstraint("cnpj REGEXP '^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}/[0-9]{4}-[0-9]{2}$'", name='valid_cnpj_format'),
        CheckConstraint("email IS NULL OR email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='valid_email_format'),
        CheckConstraint("phone IS NULL OR phone REGEXP '^[+]?[0-9\\s\\(\\)\\-]+$'", name='valid_phone_format'),
        CheckConstraint("website IS NULL OR website REGEXP '^https?://[^\\s/$.?#].[^\\s]*$'", name='valid_website_format'),
        # No constraint needed for boolean field
        CheckConstraint("LENGTH(name) >= 3", name='valid_name_length'),
        CheckConstraint("LENGTH(address) >= 10", name='valid_address_length'),
        CheckConstraint("LENGTH(contact) >= 5", name='valid_contact_length'),
    )
    
    def __repr__(self):
        return f"<Provider(id={self.id}, name='{self.name}', cnpj='{self.cnpj}', type='{self.type.value}')>"
    
    def validate_cnpj(self):
        """Validate CNPJ format and checksum"""
        if not self.cnpj:
            return False
        
        # Remove formatting
        cnpj_clean = re.sub(r'[^\d]', '', self.cnpj)
        
        if len(cnpj_clean) != 14:
            return False
        
        # Check for repeated digits
        if len(set(cnpj_clean)) == 1:
            return False
        
        # Validate checksum
        weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        # First digit
        sum_val = sum(int(cnpj_clean[i]) * weights[i] for i in range(12))
        digit = 11 - (sum_val % 11)
        if digit > 9:
            digit = 0
        
        if int(cnpj_clean[12]) != digit:
            return False
        
        # Second digit
        weights.insert(0, 6)
        sum_val = sum(int(cnpj_clean[i]) * weights[i] for i in range(13))
        digit = 11 - (sum_val % 11)
        if digit > 9:
            digit = 0
        
        if int(cnpj_clean[13]) != digit:
            return False
        
        return True 