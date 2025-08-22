from sqlalchemy import Column, Integer, String, Text, Index, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class HealthPlan(Base):
    __tablename__ = "health_plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    operator_code = Column(String(20), nullable=False, index=True)
    registration_number = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(String(26), default=func.now())
    updated_at = Column(String(26), default=func.now(), onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="health_plan", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_health_plans_name', 'name'),
        Index('idx_health_plans_operator_code', 'operator_code'),
        Index('idx_health_plans_registration_number', 'registration_number'),
        Index('idx_health_plans_active', 'active'),
        Index('idx_health_plans_created_at', 'created_at'),
        
        # Composite indexes for common queries
        Index('idx_health_plans_operator_active', 'operator_code', 'active'),
        Index('idx_health_plans_name_active', 'name', 'active'),
        Index('idx_health_plans_registration_active', 'registration_number', 'active'),
        
        # Constraints
        CheckConstraint("LENGTH(name) >= 3", name='valid_name_length'),
        CheckConstraint("LENGTH(operator_code) >= 2", name='valid_operator_code_length'),
        CheckConstraint("LENGTH(registration_number) >= 5", name='valid_registration_number_length'),
        CheckConstraint("operator_code REGEXP '^[A-Z0-9]+$'", name='valid_operator_code_format'),
        CheckConstraint("registration_number REGEXP '^[A-Z0-9\\-]+$'", name='valid_registration_number_format'),
    )
    
    def __repr__(self):
        return f"<HealthPlan(id={self.id}, name='{self.name}', operator_code='{self.operator_code}')>"
    
    @property
    def is_active(self):
        """Check if health plan is active"""
        return self.active
    
    def deactivate(self):
        """Deactivate the health plan"""
        self.active = False
        self.updated_at = func.now()
    
    def activate(self):
        """Activate the health plan"""
        self.active = True
        self.updated_at = func.now() 