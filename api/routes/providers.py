from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional

from models.database import get_db
from models.providers import Provider
from schemas.providers import ProviderCreate, ProviderResponse, ProviderUpdate, ProviderList

router = APIRouter()

@router.post("/", response_model=ProviderResponse, status_code=201)
async def create_provider(
    provider: ProviderCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new provider
    """
    try:
        # Check if CNPJ already exists
        existing_provider = db.query(Provider).filter(Provider.cnpj == provider.cnpj).first()
        if existing_provider:
            raise HTTPException(
                status_code=400,
                detail="Provider with this CNPJ already exists"
            )
        
        # Check if email already exists (if provided)
        if provider.email:
            existing_email = db.query(Provider).filter(Provider.email == provider.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=400,
                    detail="Provider with this email already exists"
                )
        
        # Create new provider
        db_provider = Provider(
            name=provider.name,
            cnpj=provider.cnpj,
            type=provider.type,
            address=provider.address,
            contact=provider.contact,
            phone=provider.phone,
            email=provider.email,
            website=provider.website,
            active=provider.active
        )
        
        db.add(db_provider)
        db.commit()
        db.refresh(db_provider)
        
        return db_provider
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating provider: {str(e)}"
        )

@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """
    Get provider by ID
    """
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Provider not found"
        )
    
    return provider

@router.get("/", response_model=ProviderList)
async def list_providers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    name: Optional[str] = Query(None, description="Filter by provider name"),
    cnpj: Optional[str] = Query(None, description="Filter by CNPJ"),
    type: Optional[str] = Query(None, description="Filter by provider type"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    List providers with optional filtering
    """
    query = db.query(Provider)
    
    # Apply filters
    if name:
        query = query.filter(Provider.name.ilike(f"%{name}%"))
    
    if cnpj:
        query = query.filter(Provider.cnpj == cnpj)
    
    if type:
        query = query.filter(Provider.type == type)
    
    if active is not None:
        query = query.filter(Provider.active == str(active).lower())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    providers = query.offset(skip).limit(limit).all()
    
    # Calculate pagination info
    pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1
    
    return ProviderList(
        items=providers,
        total=total,
        page=current_page,
        size=limit,
        pages=pages
    )

@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: int,
    provider_update: ProviderUpdate,
    db: Session = Depends(get_db)
):
    """
    Update provider information
    """
    db_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not db_provider:
        raise HTTPException(
            status_code=404,
            detail="Provider not found"
        )
    
    try:
        # Update fields if provided
        update_data = provider_update.dict(exclude_unset=True)
        
        # Check for unique constraints if updating CNPJ or email
        if 'cnpj' in update_data and update_data['cnpj'] != db_provider.cnpj:
            existing_cnpj = db.query(Provider).filter(
                and_(Provider.cnpj == update_data['cnpj'], Provider.id != provider_id)
            ).first()
            if existing_cnpj:
                raise HTTPException(
                    status_code=400,
                    detail="Provider with this CNPJ already exists"
                )
        
        if 'email' in update_data and update_data['email'] != db_provider.email:
            if update_data['email']:  # Only check if email is being set
                existing_email = db.query(Provider).filter(
                    and_(Provider.email == update_data['email'], Provider.id != provider_id)
                ).first()
                if existing_email:
                    raise HTTPException(
                        status_code=400,
                        detail="Provider with this email already exists"
                    )
        
        # Apply updates
        for field, value in update_data.items():
            setattr(db_provider, field, value)
        
        db.commit()
        db.refresh(db_provider)
        
        return db_provider
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating provider: {str(e)}"
        )

@router.delete("/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a provider
    """
    db_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not db_provider:
        raise HTTPException(
            status_code=404,
            detail="Provider not found"
        )
    
    try:
        db.delete(db_provider)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting provider: {str(e)}"
        ) 