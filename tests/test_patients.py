"""
Tests for patient creation and management.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import json
from datetime import date

from main import app
from models.database import Base, get_db
from models.patients import Patient
from schemas.patients import PatientCreate, PatientResponse


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_patients.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Create test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_auth():
    """Mock authentication for testing."""
    with patch('middleware.auth.auth_middleware') as mock_auth:
        mock_auth.authenticate.return_value = {
            "authenticated": True,
            "api_key": "test-key",
            "client_ip": "127.0.0.1"
        }
        yield mock_auth


class TestPatientCreation:
    """Test patient creation functionality."""
    
    def test_create_patient_valid_data(self, client, mock_auth):
        """Test creating a patient with valid data."""
        patient_data = {
            "name": "João Silva",
            "cpf": "12345678901",
            "birth_date": "1985-03-15",
            "phone": "(11) 98765-4321",
            "email": "joao.silva@email.com",
            "address": "Rua das Flores, 123",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01234-567"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == patient_data["name"]
        assert data["cpf"] == patient_data["cpf"]
        assert data["email"] == patient_data["email"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_patient_minimal_data(self, client, mock_auth):
        """Test creating a patient with minimal required data."""
        patient_data = {
            "name": "Maria Santos",
            "cpf": "98765432100",
            "birth_date": "1990-07-22"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == patient_data["name"]
        assert data["cpf"] == patient_data["cpf"]
        assert data["birth_date"] == patient_data["birth_date"]
    
    def test_create_patient_missing_required_fields(self, client, mock_auth):
        """Test creating a patient with missing required fields."""
        patient_data = {
            "name": "Incomplete Patient"
            # Missing cpf and birth_date
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Check that validation errors mention missing fields
        error_details = str(data["detail"])
        assert "cpf" in error_details or "birth_date" in error_details
    
    def test_create_patient_invalid_cpf_format(self, client, mock_auth):
        """Test creating a patient with invalid CPF format."""
        patient_data = {
            "name": "Invalid CPF Patient",
            "cpf": "123",  # Invalid CPF
            "birth_date": "1990-01-01"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_patient_invalid_email_format(self, client, mock_auth):
        """Test creating a patient with invalid email format."""
        patient_data = {
            "name": "Invalid Email Patient",
            "cpf": "12345678901",
            "birth_date": "1990-01-01",
            "email": "invalid-email"  # Invalid email format
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_patient_invalid_birth_date(self, client, mock_auth):
        """Test creating a patient with invalid birth date."""
        patient_data = {
            "name": "Invalid Date Patient",
            "cpf": "12345678901",
            "birth_date": "2050-01-01"  # Future date
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_patient_duplicate_cpf(self, client, mock_auth):
        """Test creating patients with duplicate CPF."""
        patient_data_1 = {
            "name": "First Patient",
            "cpf": "12345678901",
            "birth_date": "1985-03-15"
        }
        
        patient_data_2 = {
            "name": "Second Patient",
            "cpf": "12345678901",  # Same CPF
            "birth_date": "1990-07-22"
        }
        
        # Create first patient
        response1 = client.post("/api/patients/", json=patient_data_1)
        assert response1.status_code == 201
        
        # Try to create second patient with same CPF
        response2 = client.post("/api/patients/", json=patient_data_2)
        assert response2.status_code == 409  # Conflict
        data = response2.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower() or "duplicate" in data["detail"].lower()
    
    def test_create_patient_long_name(self, client, mock_auth):
        """Test creating a patient with very long name."""
        patient_data = {
            "name": "A" * 300,  # Very long name
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_patient_empty_name(self, client, mock_auth):
        """Test creating a patient with empty name."""
        patient_data = {
            "name": "",  # Empty name
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestPatientRetrieval:
    """Test patient retrieval functionality."""
    
    def test_get_patient_by_id(self, client, mock_auth):
        """Test retrieving a patient by ID."""
        # First create a patient
        patient_data = {
            "name": "Test Patient",
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        create_response = client.post("/api/patients/", json=patient_data)
        assert create_response.status_code == 201
        created_patient = create_response.json()
        patient_id = created_patient["id"]
        
        # Now retrieve the patient
        response = client.get(f"/api/patients/{patient_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient_id
        assert data["name"] == patient_data["name"]
        assert data["cpf"] == patient_data["cpf"]
    
    def test_get_patient_not_found(self, client, mock_auth):
        """Test retrieving a non-existent patient."""
        response = client.get("/api/patients/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_list_patients(self, client, mock_auth):
        """Test listing patients with pagination."""
        # Create multiple patients
        patients_data = [
            {"name": "Patient 1", "cpf": "11111111111", "birth_date": "1990-01-01"},
            {"name": "Patient 2", "cpf": "22222222222", "birth_date": "1991-01-01"},
            {"name": "Patient 3", "cpf": "33333333333", "birth_date": "1992-01-01"}
        ]
        
        for patient_data in patients_data:
            response = client.post("/api/patients/", json=patient_data)
            assert response.status_code == 201
        
        # List patients
        response = client.get("/api/patients/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["items"]) == 3
        assert data["total"] == 3
    
    def test_list_patients_with_pagination(self, client, mock_auth):
        """Test listing patients with custom pagination."""
        # Create multiple patients
        for i in range(5):
            patient_data = {
                "name": f"Patient {i+1}",
                "cpf": f"{str(i+1).zfill(11)}",
                "birth_date": "1990-01-01"
            }
            response = client.post("/api/patients/", json=patient_data)
            assert response.status_code == 201
        
        # List with pagination
        response = client.get("/api/patients/?skip=2&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 2  # (skip / limit) + 1


class TestPatientUpdate:
    """Test patient update functionality."""
    
    def test_update_patient_valid_data(self, client, mock_auth):
        """Test updating a patient with valid data."""
        # Create a patient first
        patient_data = {
            "name": "Original Name",
            "cpf": "12345678901",
            "birth_date": "1990-01-01",
            "email": "original@email.com"
        }
        
        create_response = client.post("/api/patients/", json=patient_data)
        assert create_response.status_code == 201
        patient_id = create_response.json()["id"]
        
        # Update the patient
        update_data = {
            "name": "Updated Name",
            "email": "updated@email.com",
            "phone": "(11) 99999-9999"
        }
        
        response = client.put(f"/api/patients/{patient_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["email"] == update_data["email"]
        assert data["phone"] == update_data["phone"]
        assert data["cpf"] == patient_data["cpf"]  # Should remain unchanged
    
    def test_update_patient_not_found(self, client, mock_auth):
        """Test updating a non-existent patient."""
        update_data = {
            "name": "Updated Name"
        }
        
        response = client.put("/api/patients/99999", json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestPatientDeletion:
    """Test patient deletion functionality."""
    
    def test_delete_patient(self, client, mock_auth):
        """Test deleting a patient."""
        # Create a patient first
        patient_data = {
            "name": "To Be Deleted",
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        create_response = client.post("/api/patients/", json=patient_data)
        assert create_response.status_code == 201
        patient_id = create_response.json()["id"]
        
        # Delete the patient
        response = client.delete(f"/api/patients/{patient_id}")
        
        assert response.status_code == 204
        
        # Verify patient is deleted
        get_response = client.get(f"/api/patients/{patient_id}")
        assert get_response.status_code == 404
    
    def test_delete_patient_not_found(self, client, mock_auth):
        """Test deleting a non-existent patient."""
        response = client.delete("/api/patients/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestPatientValidation:
    """Test patient data validation."""
    
    def test_patient_schema_validation(self):
        """Test PatientCreate schema validation."""
        # Valid data
        valid_data = {
            "name": "Test Patient",
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        patient = PatientCreate(**valid_data)
        assert patient.name == valid_data["name"]
        assert patient.cpf == valid_data["cpf"]
        assert patient.birth_date == date(1990, 1, 1)
    
    def test_patient_schema_validation_invalid_email(self):
        """Test PatientCreate schema validation with invalid email."""
        invalid_data = {
            "name": "Test Patient",
            "cpf": "12345678901",
            "birth_date": "1990-01-01",
            "email": "invalid-email"
        }
        
        with pytest.raises(Exception):  # Pydantic validation error
            PatientCreate(**invalid_data)
    
    def test_patient_schema_validation_future_birth_date(self):
        """Test PatientCreate schema validation with future birth date."""
        invalid_data = {
            "name": "Test Patient",
            "cpf": "12345678901",
            "birth_date": "2050-01-01"  # Future date
        }
        
        with pytest.raises(Exception):  # Pydantic validation error
            PatientCreate(**invalid_data)


class TestPatientAuthentication:
    """Test patient endpoints authentication."""
    
    def test_create_patient_without_auth(self, client):
        """Test creating a patient without authentication."""
        patient_data = {
            "name": "Test Patient",
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_patient_without_auth(self, client):
        """Test getting a patient without authentication."""
        response = client.get("/api/patients/1")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__])