from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from api.routes import health_insurance, claims, providers, patients, health_plans
from models.database import engine, Base
from services.xml_generator import TISSXMLGenerator
from middleware import (
    LoggingMiddleware,
    error_handler,
    database_error_handler
)
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="TISS Healthcare API",
    description="API for generating TISS (Troca de Informações de Saúde Suplementar) XML files",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - MUST be added FIRST, before any other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "TISS Healthcare API",
        "version": "1.0.0"
    }

# Include API routes
app.include_router(health_insurance.router, prefix="/api/health-insurance", tags=["Health Insurance"])
app.include_router(claims.router, prefix="/api/claims", tags=["Claims"])
app.include_router(providers.router, prefix="/api/providers", tags=["Providers"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(health_plans.router, prefix="/api/health-plans", tags=["Health Plans"])

# Exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    return error_handler.handle_validation_error(exc, request)

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    return error_handler.handle_database_error(exc, request)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    return error_handler.handle_generic_error(exc, request)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 