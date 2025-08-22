from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import date
from decimal import Decimal
import time

from models.database import get_db
from models.claims import Claim
from models.patients import Patient
from models.providers import Provider
from models.health_plans import HealthPlan
from schemas.claims import ClaimCreate, ClaimResponse, ClaimUpdate, ClaimList, ClaimFilter, ClaimXMLResponse
from pydantic import BaseModel
from typing import List
from services.xml_generator import TISSXMLGenerator
from middleware import require_auth, get_auth_headers, request_logger, database_error_handler

# Validation response schemas
class ValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    schema_info: dict

class SchemaInfoResponse(BaseModel):
    status: str
    file_path: str
    file_size: int
    target_namespace: str
    namespaces: dict
    root_elements: List[str]

router = APIRouter()

@router.post("/", response_model=ClaimResponse, status_code=201)
async def create_claim(
    claim: ClaimCreate,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    Create a new claim
    """
    start_time = time.time()
    
    try:
        # Log the operation
        request_logger.log_database_operation("create", "claims", success=True)
        
        # Verify patient exists
        patient = db.query(Patient).filter(Patient.id == claim.patient_id).first()
        if not patient:
            request_logger.log_database_operation("read", "patients", record_id=claim.patient_id, success=False, error="Patient not found")
            raise HTTPException(
                status_code=400,
                detail="Patient not found"
            )
        
        # Verify provider exists
        provider = db.query(Provider).filter(Provider.id == claim.provider_id).first()
        if not provider:
            request_logger.log_database_operation("read", "providers", record_id=claim.provider_id, success=False, error="Provider not found")
            raise HTTPException(
                status_code=400,
                detail="Provider not found"
            )
        
        # Verify health plan exists
        health_plan = db.query(HealthPlan).filter(HealthPlan.id == claim.plan_id).first()
        if not health_plan:
            request_logger.log_database_operation("read", "health_plans", record_id=claim.plan_id, success=False, error="Health plan not found")
            raise HTTPException(
                status_code=400,
                detail="Health plan not found"
            )
        
        # Create new claim
        db_claim = Claim(
            patient_id=claim.patient_id,
            provider_id=claim.provider_id,
            plan_id=claim.plan_id,
            procedure_code=claim.procedure_code,
            diagnosis_code=claim.diagnosis_code,
            claim_date=claim.claim_date,
            value=claim.value,
            description=claim.description,
            status=claim.status
        )
        
        db.add(db_claim)
        db.commit()
        db.refresh(db_claim)
        
        # Log successful creation
        duration = time.time() - start_time
        request_logger.log_database_operation("create", "claims", record_id=db_claim.id, success=True, duration=duration)
        
        return db_claim
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        duration = time.time() - start_time
        request_logger.log_database_operation("create", "claims", success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating claim: {str(e)}"
        )

@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: int,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    Get claim by ID
    """
    start_time = time.time()
    
    try:
        # Log database query start
        request_logger.log_database_operation("query_start", "claims", record_id=claim_id)
        
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            duration = time.time() - start_time
            request_logger.log_database_operation("query_failed", "claims", record_id=claim_id, success=False, error="Claim not found", duration=duration)
            raise HTTPException(
                status_code=404,
                detail="Claim not found"
            )
        
        # Log successful query
        duration = time.time() - start_time
        request_logger.log_database_operation("query_complete", "claims", record_id=claim_id, success=True, duration=duration)
        
        return claim
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        request_logger.log_database_operation("query_failed", "claims", record_id=claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving claim: {str(e)}"
        )

@router.get("/{claim_id}/xml", response_model=ClaimXMLResponse)
async def get_claim_xml(
    claim_id: int,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    Generate and return the claim as TISS XML
    """
    start_time = time.time()
    
    try:
        # Log XML generation start
        request_logger.log_xml_operation("generation_start", claim_id)
        
        # Generate XML using the new TISS XML generator with validation
        xml_generator = TISSXMLGenerator()
        xml_content, is_valid, validation_errors = xml_generator.generate_tiss_xml_with_validation(claim_id)
        
        if not is_valid:
            duration = time.time() - start_time
            request_logger.log_xml_operation("generation_failed", claim_id, success=False, error="XML validation failed", duration=duration)
            raise HTTPException(
                status_code=422,
                detail=f"Generated XML failed validation: {'; '.join(validation_errors)}"
            )
        
        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tiss_claim_{claim_id}_{timestamp}.xml"
        
        # Log successful generation
        duration = time.time() - start_time
        request_logger.log_xml_operation("generation_complete", claim_id, success=True, duration=duration)
        
        return ClaimXMLResponse(
            claim_id=claim_id,
            xml_content=xml_content,
            filename=filename,
            generated_at=datetime.now().isoformat()
        )
        
    except ValueError as e:
        duration = time.time() - start_time
        request_logger.log_xml_operation("generation_failed", claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        request_logger.log_xml_operation("generation_failed", claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating XML: {str(e)}"
        )

@router.get("/{claim_id}/xml/download")
async def download_claim_xml(
    claim_id: int,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    Download the claim as TISS XML file
    """
    start_time = time.time()
    
    try:
        # Log XML download start
        request_logger.log_xml_operation("download_start", claim_id)
        
        # Generate XML using the new TISS XML generator with validation
        xml_generator = TISSXMLGenerator()
        xml_content, is_valid, validation_errors = xml_generator.generate_tiss_xml_with_validation(claim_id)
        
        if not is_valid:
            duration = time.time() - start_time
            request_logger.log_xml_operation("download_failed", claim_id, success=False, error="XML validation failed", duration=duration)
            raise HTTPException(
                status_code=422,
                detail=f"Generated XML failed validation: {'; '.join(validation_errors)}"
            )
        
        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tiss_claim_{claim_id}_{timestamp}.xml"
        
        # Log successful download
        duration = time.time() - start_time
        request_logger.log_xml_operation("download_complete", claim_id, success=True, duration=duration)
        
        # Return XML file as response
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except ValueError as e:
        duration = time.time() - start_time
        request_logger.log_xml_operation("download_failed", claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        request_logger.log_xml_operation("download_failed", claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating XML: {str(e)}"
        )

@router.get("/", response_model=ClaimList)
async def list_claims(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    patient_id: Optional[int] = Query(None, description="Filter by patient ID"),
    provider_id: Optional[int] = Query(None, description="Filter by provider ID"),
    plan_id: Optional[int] = Query(None, description="Filter by health plan ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    min_value: Optional[Decimal] = Query(None, description="Filter by minimum value"),
    max_value: Optional[Decimal] = Query(None, description="Filter by maximum value"),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    List claims with optional filtering
    """
    start_time = time.time()
    
    try:
        # Log database query start
        request_logger.log_database_operation("query_start", "claims")
        
        query = db.query(Claim)
        
        # Apply filters
        if patient_id:
            query = query.filter(Claim.patient_id == patient_id)
        
        if provider_id:
            query = query.filter(Claim.provider_id == provider_id)
        
        if plan_id:
            query = query.filter(Claim.plan_id == plan_id)
        
        if status:
            query = query.filter(Claim.status == status)
        
        if start_date:
            query = query.filter(Claim.claim_date >= start_date)
        
        if end_date:
            query = query.filter(Claim.claim_date <= end_date)
        
        if min_value:
            query = query.filter(Claim.value >= min_value)
        
        if max_value:
            query = query.filter(Claim.value <= max_value)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        claims = query.offset(skip).limit(limit).all()
        
        # Calculate pagination info
        pages = (total + limit - 1) // limit
        current_page = (skip // limit) + 1
        
        # Log successful query
        duration = time.time() - start_time
        request_logger.log_database_operation("query_complete", "claims", success=True, duration=duration)
        
        return ClaimList(
            items=claims,
            total=total,
            page=current_page,
            size=limit,
            pages=pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        request_logger.log_database_operation("query_failed", "claims", success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing claims: {str(e)}"
        )

@router.put("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: int,
    claim_update: ClaimUpdate,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    Update claim information
    """
    start_time = time.time()
    
    try:
        # Log database query start
        request_logger.log_database_operation("query_start", "claims", record_id=claim_id)
        
        db_claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not db_claim:
            duration = time.time() - start_time
            request_logger.log_database_operation("query_failed", "claims", record_id=claim_id, success=False, error="Claim not found", duration=duration)
            raise HTTPException(
                status_code=404,
                detail="Claim not found"
            )
        
        # Log update start
        request_logger.log_database_operation("update_start", "claims", record_id=claim_id)
        
        # Update fields if provided
        update_data = claim_update.dict(exclude_unset=True)
        
        # Apply updates
        for field, value in update_data.items():
            setattr(db_claim, field, value)
        
        db.commit()
        db.refresh(db_claim)
        
        # Log successful update
        duration = time.time() - start_time
        request_logger.log_database_operation("update_complete", "claims", record_id=claim_id, success=True, duration=duration)
        
        return db_claim
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        duration = time.time() - start_time
        request_logger.log_database_operation("update_failed", "claims", record_id=claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error updating claim: {str(e)}"
        )

@router.delete("/{claim_id}", status_code=204)
async def delete_claim(
    claim_id: int,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    Delete a claim
    """
    start_time = time.time()
    
    try:
        # Log database query start
        request_logger.log_database_operation("query_start", "claims", record_id=claim_id)
        
        db_claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not db_claim:
            duration = time.time() - start_time
            request_logger.log_database_operation("query_failed", "claims", record_id=claim_id, success=False, error="Claim not found", duration=duration)
            raise HTTPException(
                status_code=404,
                detail="Claim not found"
            )
        
        # Log delete start
        request_logger.log_database_operation("delete_start", "claims", record_id=claim_id)
        
        db.delete(db_claim)
        db.commit()
        
        # Log successful delete
        duration = time.time() - start_time
        request_logger.log_database_operation("delete_complete", "claims", record_id=claim_id, success=True, duration=duration)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        duration = time.time() - start_time
        request_logger.log_database_operation("delete_failed", "claims", record_id=claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting claim: {str(e)}"
        )

# Validation endpoints
@router.get("/schema/info", response_model=SchemaInfoResponse)
async def get_schema_info(
    request: Request,
    auth: dict = Depends(require_auth)
):
    """
    Get information about the loaded TISS XSD schema
    """
    start_time = time.time()
    
    try:
        # Log schema info request
        request_logger.log_validation_operation("schema_info_request")
        
        xml_generator = TISSXMLGenerator()
        schema_info = xml_generator.get_schema_info()
        
        if schema_info["status"] == "loaded":
            # Log successful schema info retrieval
            duration = time.time() - start_time
            request_logger.log_validation_operation("schema_info_success", success=True, duration=duration)
            return SchemaInfoResponse(**schema_info)
        else:
            duration = time.time() - start_time
            request_logger.log_validation_operation("schema_info_failed", success=False, error="Schema not loaded", duration=duration)
            raise HTTPException(
                status_code=500,
                detail=f"Schema not loaded: {schema_info.get('message', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        request_logger.log_validation_operation("schema_info_failed", success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting schema info: {str(e)}"
        )

@router.post("/validate/xml", response_model=ValidationResponse)
async def validate_xml_content(
    xml_content: str,
    request: Request,
    auth: dict = Depends(require_auth)
):
    """
    Validate XML content against TISS XSD schema
    """
    start_time = time.time()
    
    try:
        # Log XML validation start
        request_logger.log_validation_operation("xml_validation_start", content_length=len(xml_content))
        
        xml_generator = TISSXMLGenerator()
        is_valid, validation_errors = xml_generator.validate_generated_xml(xml_content)
        schema_info = xml_generator.get_schema_info()
        
        # Log validation result
        duration = time.time() - start_time
        if is_valid:
            request_logger.log_validation_operation("xml_validation_success", success=True, duration=duration)
        else:
            request_logger.log_validation_operation("xml_validation_failed", success=False, error_count=len(validation_errors), duration=duration)
        
        return ValidationResponse(
            is_valid=is_valid,
            errors=validation_errors,
            schema_info=schema_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        request_logger.log_validation_operation("xml_validation_failed", success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error validating XML: {str(e)}"
        )

@router.get("/{claim_id}/xml/validate", response_model=ValidationResponse)
async def validate_claim_xml(
    claim_id: int,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    Generate and validate TISS XML for a specific claim
    """
    start_time = time.time()
    
    try:
        # Log claim XML validation start
        request_logger.log_validation_operation("claim_validation_start", claim_id=claim_id)
        
        xml_generator = TISSXMLGenerator()
        xml_content, is_valid, validation_errors = xml_generator.generate_tiss_xml_with_validation(claim_id)
        schema_info = xml_generator.get_schema_info()
        
        # Log validation result
        duration = time.time() - start_time
        if is_valid:
            request_logger.log_validation_operation("claim_validation_success", claim_id=claim_id, success=True, duration=duration)
        else:
            request_logger.log_validation_operation("claim_validation_failed", claim_id=claim_id, success=False, error_count=len(validation_errors), duration=duration)
        
        return ValidationResponse(
            is_valid=is_valid,
            errors=validation_errors,
            schema_info=schema_info
        )
        
    except ValueError as e:
        duration = time.time() - start_time
        request_logger.log_validation_operation("claim_validation_failed", claim_id=claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        request_logger.log_validation_operation("claim_validation_failed", claim_id=claim_id, success=False, error=str(e), duration=duration)
        raise HTTPException(
            status_code=500,
            detail=f"Error validating claim XML: {str(e)}"
        ) 