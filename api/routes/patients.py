from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date

from models.database import get_db
from models.patients import Patient
from schemas.patients import PatientCreate, PatientResponse, PatientUpdate, PatientList

router = APIRouter()

@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new patient
    """
    try:
        # Check if CPF already exists
        existing_patient = db.query(Patient).filter(Patient.cpf == patient.cpf).first()
        if existing_patient:
            raise HTTPException(
                status_code=400,
                detail="Patient with this CPF already exists"
            )
        
        # Check if email already exists
        existing_email = db.query(Patient).filter(Patient.email == patient.email).first()
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Patient with this email already exists"
            )
        
        # Create new patient
        db_patient = Patient(
            name=patient.name,
            cpf=patient.cpf,
            birth_date=patient.birth_date,
            address=patient.address,
            phone=patient.phone,
            email=patient.email
        )
        
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        
        return db_patient
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating patient: {str(e)}"
        )

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Get patient by ID
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
    
    return patient

@router.get("/", response_model=PatientList)
async def list_patients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    name: Optional[str] = Query(None, description="Filter by patient name"),
    cpf: Optional[str] = Query(None, description="Filter by CPF"),
    email: Optional[str] = Query(None, description="Filter by email"),
    db: Session = Depends(get_db)
):
    """
    List patients with optional filtering
    """
    query = db.query(Patient)
    
    # Apply filters
    if name:
        query = query.filter(Patient.name.ilike(f"%{name}%"))
    
    if cpf:
        query = query.filter(Patient.cpf == cpf)
    
    if email:
        query = query.filter(Patient.email == email)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    patients = query.offset(skip).limit(limit).all()
    
    # Calculate pagination info
    pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1
    
    return PatientList(
        items=patients,
        total=total,
        page=current_page,
        size=limit,
        pages=pages
    )

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db)
):
    """
    Update patient information
    """
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
    
    try:
        # Update fields if provided
        update_data = patient_update.dict(exclude_unset=True)
        
        # Check for unique constraints if updating CPF or email
        if 'cpf' in update_data and update_data['cpf'] != db_patient.cpf:
            existing_cpf = db.query(Patient).filter(
                and_(Patient.cpf == update_data['cpf'], Patient.id != patient_id)
            ).first()
            if existing_cpf:
                raise HTTPException(
                    status_code=400,
                    detail="Patient with this CPF already exists"
                )
        
        if 'email' in update_data and update_data['email'] != db_patient.email:
            existing_email = db.query(Patient).filter(
                and_(Patient.email == update_data['email'], Patient.id != patient_id)
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=400,
                    detail="Patient with this email already exists"
                )
        
        # Apply updates
        for field, value in update_data.items():
            setattr(db_patient, field, value)
        
        db.commit()
        db.refresh(db_patient)
        
        return db_patient
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating patient: {str(e)}"
        )

@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a patient
    """
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
    
    try:
        db.delete(db_patient)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting patient: {str(e)}"
        ) 