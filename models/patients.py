from sqlalchemy import Column, Integer, String, Date, Text, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import re


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    cpf = Column(String(14), nullable=False, unique=True, index=True)  # Format: XXX.XXX.XXX-XX
    birth_date = Column(Date, nullable=False, index=True)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    created_at = Column(String(26), default=func.now())
    updated_at = Column(String(26), default=func.now(), onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="patient", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_patients_cpf', 'cpf'),
        Index('idx_patients_name', 'name'),
        Index('idx_patients_email', 'email'),
        Index('idx_patients_birth_date', 'birth_date'),
        Index('idx_patients_created_at', 'created_at'),
        
        # Composite indexes for common queries
        Index('idx_patients_name_cpf', 'name', 'cpf'),
        Index('idx_patients_cpf_email', 'cpf', 'email'),
        
        # Constraints
        CheckConstraint("cpf REGEXP '^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2}$'", name='valid_cpf_format'),
        CheckConstraint("email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='valid_email_format'),
        # Phone validation removed - MySQL regex constraints can be problematic
        CheckConstraint("LENGTH(name) >= 2", name='valid_name_length'),
        CheckConstraint("LENGTH(address) >= 10", name='valid_address_length'),
    )
    
    def __repr__(self):
        return f"<Patient(id={self.id}, name='{self.name}', cpf='{self.cpf}')>"
    
    @property
    def age(self):
        """Calculate patient age based on birth date"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
    
    def validate_cpf(self):
        """Validate CPF format and checksum"""
        if not self.cpf:
            return False
        
        # Remove formatting
        cpf_clean = re.sub(r'[^\d]', '', self.cpf)
        
        if len(cpf_clean) != 11:
            return False
        
        # Check for repeated digits
        if len(set(cpf_clean)) == 1:
            return False
        
        # Validate checksum
        for i in range(9, 11):
            value = sum((int(cpf_clean[num]) * ((i + 1) - num) for num in range(0, i)))
            digit = ((value * 10) % 11) % 10
            if int(cpf_clean[i]) != digit:
                return False
        
        return True 