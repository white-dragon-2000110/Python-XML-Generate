from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from models.database import get_db
from models.health_insurance import HealthInsurance, Contract
from schemas.health_insurance import (
    HealthInsuranceCreate, 
    HealthInsuranceUpdate, 
    HealthInsuranceResponse,
    HealthInsuranceList,
    ContractCreate,
    ContractUpdate,
    ContractResponse
)

router = APIRouter()

@router.post("/", response_model=HealthInsuranceResponse)
async def create_health_insurance(
    health_insurance: HealthInsuranceCreate,
    db: Session = Depends(get_db)
):
    """Create a new health insurance company"""
    try:
        # Check if CNPJ already exists
        existing = db.query(HealthInsurance).filter(
            HealthInsurance.cnpj == health_insurance.cnpj
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="CNPJ already registered")
        
        # Check if ANS code already exists
        existing_ans = db.query(HealthInsurance).filter(
            HealthInsurance.ans_code == health_insurance.ans_code
        ).first()
        
        if existing_ans:
            raise HTTPException(status_code=400, detail="ANS code already registered")
        
        # Create new health insurance
        db_health_insurance = HealthInsurance(**health_insurance.dict())
        db.add(db_health_insurance)
        db.commit()
        db.refresh(db_health_insurance)
        
        return db_health_insurance
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=HealthInsuranceList)
async def list_health_insurances(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List health insurance companies with pagination"""
    try:
        query = db.query(HealthInsurance)
        
        if active_only:
            query = query.filter(HealthInsurance.is_active == True)
        
        total = query.count()
        health_insurances = query.offset(skip).limit(limit).all()
        
        pages = (total + limit - 1) // limit
        current_page = (skip // limit) + 1
        
        return HealthInsuranceList(
            items=health_insurances,
            total=total,
            page=current_page,
            size=limit,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{health_insurance_id}", response_model=HealthInsuranceResponse)
async def get_health_insurance(
    health_insurance_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific health insurance company by ID"""
    try:
        health_insurance = db.query(HealthInsurance).filter(
            HealthInsurance.id == health_insurance_id
        ).first()
        
        if not health_insurance:
            raise HTTPException(status_code=404, detail="Health insurance not found")
        
        return health_insurance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{health_insurance_id}", response_model=HealthInsuranceResponse)
async def update_health_insurance(
    health_insurance_id: int,
    health_insurance_update: HealthInsuranceUpdate,
    db: Session = Depends(get_db)
):
    """Update a health insurance company"""
    try:
        db_health_insurance = db.query(HealthInsurance).filter(
            HealthInsurance.id == health_insurance_id
        ).first()
        
        if not db_health_insurance:
            raise HTTPException(status_code=404, detail="Health insurance not found")
        
        # Update fields
        update_data = health_insurance_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_health_insurance, field, value)
        
        db.commit()
        db.refresh(db_health_insurance)
        
        return db_health_insurance
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{health_insurance_id}")
async def delete_health_insurance(
    health_insurance_id: int,
    db: Session = Depends(get_db)
):
    """Delete a health insurance company (soft delete)"""
    try:
        db_health_insurance = db.query(HealthInsurance).filter(
            HealthInsurance.id == health_insurance_id
        ).first()
        
        if not db_health_insurance:
            raise HTTPException(status_code=404, detail="Health insurance not found")
        
        # Soft delete - set as inactive
        db_health_insurance.is_active = False
        db.commit()
        
        return {"message": "Health insurance deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{health_insurance_id}/contracts", response_model=ContractResponse)
async def create_contract(
    health_insurance_id: int,
    contract: ContractCreate,
    db: Session = Depends(get_db)
):
    """Create a new contract for a health insurance company"""
    try:
        # Verify health insurance exists
        health_insurance = db.query(HealthInsurance).filter(
            HealthInsurance.id == health_insurance_id
        ).first()
        
        if not health_insurance:
            raise HTTPException(status_code=404, detail="Health insurance not found")
        
        # Create contract
        db_contract = Contract(**contract.dict())
        db.add(db_contract)
        db.commit()
        db.refresh(db_contract)
        
        return db_contract
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{health_insurance_id}/contracts", response_model=List[ContractResponse])
async def list_contracts(
    health_insurance_id: int,
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List contracts for a health insurance company"""
    try:
        query = db.query(Contract).filter(
            Contract.health_insurance_id == health_insurance_id
        )
        
        if active_only:
            query = query.filter(Contract.is_active == True)
        
        contracts = query.all()
        return contracts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 