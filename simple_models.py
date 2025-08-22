from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    cnpj = Column(String(18), nullable=False)
    type = Column(String(50), nullable=False)
    address = Column(Text, nullable=False)
    contact = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    cpf = Column(String(14), nullable=False)
    birth_date = Column(String(10), nullable=False)
    gender = Column(String(10), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, nullable=False)
    provider_id = Column(Integer, nullable=False)
    claim_number = Column(String(50), nullable=False)
    claim_date = Column(String(10), nullable=False)
    total_amount = Column(String(20), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class HealthPlan(Base):
    __tablename__ = "health_plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    operator_code = Column(String(10), nullable=False)
    registration_number = Column(String(20), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 