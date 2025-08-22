import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, get_db
from main import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_health_insurance(setup_database):
    """Test creating a health insurance company"""
    health_insurance_data = {
        "cnpj": "12.345.678/0001-90",
        "name": "Test Health Insurance",
        "trade_name": "TestHealth",
        "ans_code": "123456",
        "address": "123 Test Street",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01234-567",
        "phone": "(11) 1234-5678",
        "email": "test@testhealth.com",
        "website": "https://testhealth.com",
        "is_active": True
    }
    
    response = client.post("/api/v1/health-insurance/", json=health_insurance_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["cnpj"] == health_insurance_data["cnpj"]
    assert data["name"] == health_insurance_data["name"]
    assert data["ans_code"] == health_insurance_data["ans_code"]

def test_create_health_insurance_duplicate_cnpj(setup_database):
    """Test creating health insurance with duplicate CNPJ"""
    health_insurance_data = {
        "cnpj": "12.345.678/0001-90",
        "name": "Test Health Insurance",
        "ans_code": "123456"
    }
    
    # Create first health insurance
    response = client.post("/api/v1/health-insurance/", json=health_insurance_data)
    assert response.status_code == 200
    
    # Try to create second with same CNPJ
    response = client.post("/api/v1/health-insurance/", json=health_insurance_data)
    assert response.status_code == 400
    assert "CNPJ already registered" in response.json()["detail"]

def test_list_health_insurances(setup_database):
    """Test listing health insurance companies"""
    # Create test data
    health_insurance_data = {
        "cnpj": "12.345.678/0001-90",
        "name": "Test Health Insurance",
        "ans_code": "123456"
    }
    
    client.post("/api/v1/health-insurance/", json=health_insurance_data)
    
    # List health insurances
    response = client.get("/api/v1/health-insurance/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert data["page"] == 1

def test_get_health_insurance(setup_database):
    """Test getting a specific health insurance company"""
    # Create test data
    health_insurance_data = {
        "cnpj": "12.345.678/0001-90",
        "name": "Test Health Insurance",
        "ans_code": "123456"
    }
    
    create_response = client.post("/api/v1/health-insurance/", json=health_insurance_data)
    health_insurance_id = create_response.json()["id"]
    
    # Get health insurance
    response = client.get(f"/api/v1/health-insurance/{health_insurance_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == health_insurance_id
    assert data["cnpj"] == health_insurance_data["cnpj"]

def test_update_health_insurance(setup_database):
    """Test updating a health insurance company"""
    # Create test data
    health_insurance_data = {
        "cnpj": "12.345.678/0001-90",
        "name": "Test Health Insurance",
        "ans_code": "123456"
    }
    
    create_response = client.post("/api/v1/health-insurance/", json=health_insurance_data)
    health_insurance_id = create_response.json()["id"]
    
    # Update health insurance
    update_data = {"name": "Updated Health Insurance"}
    response = client.put(f"/api/v1/health-insurance/{health_insurance_id}", json=update_data)
    assert response.status_code == 200
    
    # Verify update
    get_response = client.get(f"/api/v1/health-insurance/{health_insurance_id}")
    data = get_response.json()
    assert data["name"] == "Updated Health Insurance"

def test_delete_health_insurance(setup_database):
    """Test deleting a health insurance company"""
    # Create test data
    health_insurance_data = {
        "cnpj": "12.345.678/0001-90",
        "name": "Test Health Insurance",
        "ans_code": "123456"
    }
    
    create_response = client.post("/api/v1/health-insurance/", json=health_insurance_data)
    health_insurance_id = create_response.json()["id"]
    
    # Delete health insurance
    response = client.delete(f"/api/v1/health-insurance/{health_insurance_id}")
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "TISS Healthcare API" 