from sqlalchemy import Column, Integer, String, Date, Numeric, Text, Index, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("health_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    procedure_code = Column(String(20), nullable=True, index=True)
    diagnosis_code = Column(String(20), nullable=True, index=True)
    claim_date = Column(Date, nullable=False, index=True)
    value = Column(Numeric(10, 2), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, approved, denied, paid
    created_at = Column(String(26), default=func.now())
    updated_at = Column(String(26), default=func.now(), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="claims")
    provider = relationship("Provider", back_populates="claims")
    health_plan = relationship("HealthPlan", back_populates="claims")
    
    # Indexes
    __table_args__ = (
        Index('idx_claims_patient_id', 'patient_id'),
        Index('idx_claims_provider_id', 'provider_id'),
        Index('idx_claims_plan_id', 'plan_id'),
        Index('idx_claims_procedure_code', 'procedure_code'),
        Index('idx_claims_diagnosis_code', 'diagnosis_code'),
        Index('idx_claims_claim_date', 'claim_date'),
        Index('idx_claims_value', 'value'),
        Index('idx_claims_status', 'status'),
        Index('idx_claims_created_at', 'created_at'),
        
        # Composite indexes for common queries
        Index('idx_claims_patient_date', 'patient_id', 'claim_date'),
        Index('idx_claims_provider_date', 'provider_id', 'claim_date'),
        Index('idx_claims_plan_date', 'plan_id', 'claim_date'),
        Index('idx_claims_procedure_diagnosis', 'procedure_code', 'diagnosis_code'),
        Index('idx_claims_date_status', 'claim_date', 'status'),
        Index('idx_claims_patient_status', 'patient_id', 'status'),
        Index('idx_claims_provider_status', 'provider_id', 'status'),
        Index('idx_claims_plan_status', 'plan_id', 'status'),
        
        # Constraints
        CheckConstraint("value > 0", name='valid_claim_value'),
        # Note: claim_date validation removed - MySQL doesn't support CURDATE() in CHECK constraints
        CheckConstraint("status IN ('pending', 'approved', 'denied', 'paid')", name='valid_claim_status'),
        CheckConstraint("procedure_code IS NULL OR LENGTH(procedure_code) >= 3", name='valid_procedure_code_length'),
        CheckConstraint("diagnosis_code IS NULL OR LENGTH(diagnosis_code) >= 3", name='valid_diagnosis_code_length'),
        CheckConstraint("procedure_code IS NULL OR procedure_code REGEXP '^[A-Z0-9\\-]+$'", name='valid_procedure_code_format'),
        CheckConstraint("diagnosis_code IS NULL OR diagnosis_code REGEXP '^[A-Z0-9\\-]+$'", name='valid_diagnosis_code_format'),
    )
    
    def __repr__(self):
        return f"<Claim(id={self.id}, patient_id={self.patient_id}, provider_id={self.provider_id}, value={self.value})>"
    
    @property
    def is_pending(self):
        """Check if claim is pending"""
        return self.status == "pending"
    
    @property
    def is_approved(self):
        """Check if claim is approved"""
        return self.status == "approved"
    
    @property
    def is_denied(self):
        """Check if claim is denied"""
        return self.status == "denied"
    
    @property
    def is_paid(self):
        """Check if claim is paid"""
        return self.status == "paid"
    
    def approve(self):
        """Approve the claim"""
        self.status = "approved"
        self.updated_at = func.now()
    
    def deny(self):
        """Deny the claim"""
        self.status = "denied"
        self.updated_at = func.now()
    
    def mark_as_paid(self):
        """Mark claim as paid"""
        if self.status == "approved":
            self.status = "paid"
            self.updated_at = func.now()
        else:
            raise ValueError("Only approved claims can be marked as paid")
    
    def get_total_value(self):
        """Get the total value of the claim"""
        return float(self.value) 