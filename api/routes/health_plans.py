from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db
from models.health_plans import HealthPlan
from schemas.health_plans import HealthPlanCreate, HealthPlanResponse, HealthPlanUpdate, HealthPlanList

router = APIRouter()

@router.post("/", response_model=HealthPlanResponse)
async def create_health_plan(
    plan: HealthPlanCreate,
    db: Session = Depends(get_db)
):
    """Create a new health plan"""
    try:
        db_plan = HealthPlan(**plan.dict())
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return db_plan
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating health plan: {str(e)}"
        )

@router.get("/", response_model=HealthPlanList)
async def list_health_plans(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List health plans with pagination"""
    try:
        total = db.query(HealthPlan).count()
        plans = db.query(HealthPlan).offset(skip).limit(limit).all()
        
        pages = (total + limit - 1) // limit
        current_page = (skip // limit) + 1
        
        return HealthPlanList(
            items=plans,
            total=total,
            page=current_page,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing health plans: {str(e)}"
        )

@router.get("/{plan_id}", response_model=HealthPlanResponse)
async def get_health_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific health plan"""
    db_plan = db.query(HealthPlan).filter(HealthPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=404,
            detail="Health plan not found"
        )
    return db_plan

@router.put("/{plan_id}", response_model=HealthPlanResponse)
async def update_health_plan(
    plan_id: int,
    plan_update: HealthPlanUpdate,
    db: Session = Depends(get_db)
):
    """Update a health plan"""
    db_plan = db.query(HealthPlan).filter(HealthPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=404,
            detail="Health plan not found"
        )
    
    try:
        for field, value in plan_update.dict(exclude_unset=True).items():
            setattr(db_plan, field, value)
        
        db.commit()
        db.refresh(db_plan)
        return db_plan
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating health plan: {str(e)}"
        )

@router.delete("/{plan_id}", status_code=204)
async def delete_health_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """Delete a health plan"""
    db_plan = db.query(HealthPlan).filter(HealthPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=404,
            detail="Health plan not found"
        )
    
    try:
        db.delete(db_plan)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting health plan: {str(e)}"
        )