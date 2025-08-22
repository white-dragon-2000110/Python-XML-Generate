from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import database and models
from database import get_db, engine
from simple_models import Base, Patient, Claim, Provider, HealthPlan

# Create FastAPI app
app = FastAPI(title="TISS Healthcare API (SQLite)", version="1.0.0")

# CORS middleware - Proper configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware to ensure CORS headers
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Create database tables
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ SQLite database connected successfully")
        print("🗄️ Database file: tiss_healthcare.db")
    except Exception as e:
        print(f"❌ Database error: {e}")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "sqlite_connected"}



# Providers endpoints
@app.get("/api/providers")
async def get_providers(db: Session = Depends(get_db)):
    """Get all providers from database"""
    try:
        providers = db.query(Provider).all()
        return {"items": providers, "total": len(providers)}
    except Exception as e:
        print(f"Error getting providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/providers")
async def create_provider(provider_data: dict, db: Session = Depends(get_db)):
    """Create provider in database"""
    try:
        print(f"Creating provider: {provider_data}")
        provider = Provider(**provider_data)
        db.add(provider)
        db.commit()
        db.refresh(provider)
        print(f"Provider created with ID: {provider.id}")
        return provider
    except Exception as e:
        db.rollback()
        print(f"Error creating provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/providers/{provider_id}")
async def update_provider(provider_id: int, provider_data: dict, db: Session = Depends(get_db)):
    """Update provider in database"""
    try:
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        for field, value in provider_data.items():
            setattr(provider, field, value)
        
        db.commit()
        db.refresh(provider)
        return provider
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    """Delete provider from database"""
    try:
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        db.delete(provider)
        db.commit()
        return {"message": f"Provider {provider_id} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Patients endpoints
@app.get("/api/patients")
async def get_patients(db: Session = Depends(get_db)):
    """Get all patients from database"""
    try:
        patients = db.query(Patient).all()
        return {"items": patients, "total": len(patients)}
    except Exception as e:
        print(f"Error getting patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/patients")
async def create_patient(patient_data: dict, db: Session = Depends(get_db)):
    """Create patient in database"""
    try:
        print(f"Creating patient: {patient_data}")
        patient = Patient(**patient_data)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        print(f"Patient created with ID: {patient.id}")
        return patient
    except Exception as e:
        db.rollback()
        print(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/patients/{patient_id}")
async def update_patient(patient_id: int, patient_data: dict, db: Session = Depends(get_db)):
    """Update patient in database"""
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        for field, value in patient_data.items():
            setattr(patient, field, value)
        
        db.commit()
        db.refresh(patient)
        return patient
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/patients/{patient_id}")
async def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    """Delete patient from database"""
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        db.delete(patient)
        db.commit()
        return {"message": f"Patient {patient_id} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Claims endpoints
@app.get("/api/claims")
async def get_claims(db: Session = Depends(get_db)):
    """Get all claims from database"""
    try:
        claims = db.query(Claim).all()
        return {"items": claims, "total": len(claims)}
    except Exception as e:
        print(f"Error getting claims: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/claims")
async def create_claim(claim_data: dict, db: Session = Depends(get_db)):
    """Create claim in database"""
    try:
        print(f"Creating claim: {claim_data}")
        claim = Claim(**claim_data)
        db.add(claim)
        db.commit()
        db.refresh(claim)
        print(f"Claim created with ID: {claim.id}")
        return claim
    except Exception as e:
        db.rollback()
        print(f"Error creating claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/claims/{claim_id}")
async def update_claim(claim_id: int, claim_data: dict, db: Session = Depends(get_db)):
    """Update claim in database"""
    try:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        for field, value in claim_data.items():
            setattr(claim, field, value)
        
        db.commit()
        db.refresh(claim)
        return claim
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/claims/{claim_id}")
async def delete_claim(claim_id: int, db: Session = Depends(get_db)):
    """Delete claim from database"""
    try:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        db.delete(claim)
        db.commit()
        return {"message": f"Claim {claim_id} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Health plans endpoints
@app.get("/api/health-plans")
async def get_health_plans(db: Session = Depends(get_db)):
    """Get all health plans from database"""
    try:
        plans = db.query(HealthPlan).all()
        return {"items": plans, "total": len(plans)}
    except Exception as e:
        print(f"Error getting health plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/health-plans")
async def create_health_plan(plan_data: dict, db: Session = Depends(get_db)):
    """Create health plan in database"""
    try:
        print(f"Creating health plan: {plan_data}")
        plan = HealthPlan(**plan_data)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        print(f"Health plan created with ID: {plan.id}")
        return plan
    except Exception as e:
        db.rollback()
        print(f"Error creating health plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/health-plans/{plan_id}")
async def update_health_plan(plan_id: int, plan_data: dict, db: Session = Depends(get_db)):
    """Update health plan in database"""
    try:
        plan = db.query(HealthPlan).filter(HealthPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Health plan not found")
        
        for field, value in plan_data.items():
            setattr(plan, field, value)
        
        db.commit()
        db.refresh(plan)
        return plan
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/health-plans/{plan_id}")
async def delete_health_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete health plan from database"""
    try:
        plan = db.query(HealthPlan).filter(HealthPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Health plan not found")
        
        db.delete(plan)
        db.commit()
        return {"message": f"Health plan {plan_id} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting TISS Healthcare API with SQLite...")
    print("📍 Host: 0.0.0.0")
    print("🔌 Port: 8000")
    print("🌐 CORS enabled for frontend")
    print("🗄️ Using SQLite database (no setup required)")
    print("=" * 50)
    
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True) 