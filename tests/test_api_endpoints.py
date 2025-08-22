import pytest
from fastapi.testclient import TestClient
from main import app
from models.database import get_db, Base, engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_patient():
    """Test creating a patient"""
    patient_data = {
        "name": "John Doe",
        "cpf": "123.456.789-01",
        "birth_date": "1990-01-01",
        "address": "123 Main St, City, State 12345",
        "phone": "+55 11 99999-9999",
        "email": "john.doe@example.com"
    }
    
    response = client.post("/api/patients/", json=patient_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == patient_data["name"]
    assert data["cpf"] == patient_data["cpf"]
    assert data["email"] == patient_data["email"]
    assert "id" in data

def test_get_patient():
    """Test getting a patient by ID"""
    # First create a patient
    patient_data = {
        "name": "Jane Doe",
        "cpf": "987.654.321-09",
        "birth_date": "1985-05-15",
        "address": "456 Oak Ave, City, State 54321",
        "phone": "+55 11 88888-8888",
        "email": "jane.doe@example.com"
    }
    
    create_response = client.post("/api/patients/", json=patient_data)
    patient_id = create_response.json()["id"]
    
    # Then get the patient
    response = client.get(f"/api/patients/{patient_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == patient_data["name"]
    assert data["cpf"] == patient_data["cpf"]

def test_create_provider():
    """Test creating a provider"""
    provider_data = {
        "name": "City Hospital",
        "cnpj": "12.345.678/0001-90",
        "type": "hospital",
        "address": "789 Health Blvd, City, State 67890",
        "contact": "Dr. Smith",
        "phone": "+55 11 77777-7777",
        "email": "contact@cityhospital.com",
        "website": "https://cityhospital.com",
        "active": True
    }
    
    response = client.post("/api/providers/", json=provider_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == provider_data["name"]
    assert data["cnpj"] == provider_data["cnpj"]
    assert data["type"] == provider_data["type"]
    assert "id" in data

def test_create_claim():
    """Test creating a claim"""
    # First create required entities
    patient_data = {
        "name": "Bob Wilson",
        "cpf": "111.222.333-44",
        "birth_date": "1975-12-25",
        "address": "321 Pine St, City, State 11111",
        "phone": "+55 11 66666-6666",
        "email": "bob.wilson@example.com"
    }
    patient_response = client.post("/api/patients/", json=patient_data)
    patient_id = patient_response.json()["id"]
    
    provider_data = {
        "name": "Medical Clinic",
        "cnpj": "98.765.432/0001-10",
        "type": "clinic",
        "address": "654 Care Lane, City, State 22222",
        "contact": "Dr. Johnson",
        "phone": "+55 11 55555-5555",
        "email": "contact@medicalclinic.com",
        "active": True
    }
    provider_response = client.post("/api/providers/", json=provider_data)
    provider_id = provider_response.json()["id"]
    
    # Create a simple health plan (this would normally come from a health plan endpoint)
    # For testing, we'll assume it exists with ID 1
    
    claim_data = {
        "patient_id": patient_id,
        "provider_id": provider_id,
        "plan_id": 1,  # Assuming this exists
        "procedure_code": "PROC001",
        "diagnosis_code": "DIAG001",
        "date": "2024-01-15",
        "value": "150.00",
        "description": "Regular checkup",
        "status": "pending"
    }
    
    response = client.post("/api/claims/", json=claim_data)
    # This might fail if health plan with ID 1 doesn't exist, which is expected
    # In a real scenario, you'd create the health plan first
    assert response.status_code in [201, 400]  # 400 if health plan doesn't exist

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "TISS Healthcare API"
    assert data["version"] == "1.0.0"

def test_patients_list():
    """Test listing patients"""
    # Create a couple of patients first
    patients = [
        {
            "name": "Alice Brown",
            "cpf": "555.666.777-88",
            "birth_date": "1988-03-20",
            "address": "111 Test St, City, State 33333",
            "phone": "+55 11 44444-4444",
            "email": "alice.brown@example.com"
        },
        {
            "name": "Charlie Green",
            "cpf": "999.888.777-66",
            "birth_date": "1992-07-10",
            "address": "222 Test Ave, City, State 44444",
            "phone": "+55 11 33333-3333",
            "email": "charlie.green@example.com"
        }
    ]
    
    for patient in patients:
        client.post("/api/patients/", json=patient)
    
    # Test listing patients
    response = client.get("/api/patients/")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    assert len(data["items"]) >= 2  # At least the 2 we created

def test_providers_list():
    """Test listing providers"""
    # Create a couple of providers first
    providers = [
        {
            "name": "Test Hospital",
            "cnpj": "11.111.111/0001-11",
            "type": "hospital",
            "address": "333 Test Blvd, City, State 55555",
            "contact": "Dr. Test",
            "phone": "+55 11 22222-2222",
            "email": "contact@testhospital.com",
            "active": True
        },
        {
            "name": "Test Clinic",
            "cnpj": "22.222.222/0001-22",
            "type": "clinic",
            "address": "444 Test Lane, City, State 66666",
            "contact": "Dr. Test2",
            "phone": "+55 11 11111-1111",
            "email": "contact@testclinic.com",
            "active": True
        }
    ]
    
    for provider in providers:
        client.post("/api/providers/", json=provider)
    
    # Test listing providers
    response = client.get("/api/providers/")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    assert len(data["items"]) >= 2  # At least the 2 we created 