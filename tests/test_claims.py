"""
Tests for claim creation and management.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import json
from datetime import date, datetime
from decimal import Decimal

from main import app
from models.database import Base, get_db
from models.claims import Claim
from models.patients import Patient
from models.providers import Provider
from models.health_plans import HealthPlan
from schemas.claims import ClaimCreate, ClaimResponse


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_claims.db"
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


@pytest.fixture
def sample_patient(client, mock_auth):
    """Create a sample patient for testing."""
    patient_data = {
        "name": "João Silva",
        "cpf": "12345678901",
        "birth_date": "1985-03-15",
        "email": "joao@email.com"
    }
    
    response = client.post("/api/patients/", json=patient_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_provider(client, mock_auth):
    """Create a sample provider for testing."""
    provider_data = {
        "name": "Hospital São Paulo",
        "cnpj": "12345678000195",
        "cnes": "1234567",
        "provider_type": "hospital",
        "address": "Rua da Saúde, 123",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01234-567"
    }
    
    response = client.post("/api/providers/", json=provider_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sample_health_plan(client, mock_auth):
    """Create a sample health plan for testing."""
    health_plan_data = {
        "name": "Plano Premium",
        "ans_code": "123456",
        "plan_type": "individual",
        "coverage_type": "medical_hospital",
        "is_active": True
    }
    
    response = client.post("/api/health-insurance/", json=health_plan_data)
    assert response.status_code == 201
    return response.json()


class TestClaimCreation:
    """Test claim creation functionality."""
    
    def test_create_claim_valid_data(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test creating a claim with valid data."""
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "150.00",
            "description": "Consulta médica",
            "status": "pending"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == claim_data["patient_id"]
        assert data["provider_id"] == claim_data["provider_id"]
        assert data["plan_id"] == claim_data["plan_id"]
        assert data["procedure_code"] == claim_data["procedure_code"]
        assert data["diagnosis_code"] == claim_data["diagnosis_code"]
        assert float(data["value"]) == float(claim_data["value"])
        assert data["status"] == claim_data["status"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_claim_minimal_data(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test creating a claim with minimal required data."""
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == claim_data["patient_id"]
        assert data["status"] == "pending"  # Default status
    
    def test_create_claim_missing_required_fields(self, client, mock_auth):
        """Test creating a claim with missing required fields."""
        claim_data = {
            "procedure_code": "40101019",
            "value": "100.00"
            # Missing patient_id, provider_id, plan_id, etc.
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Check that validation errors mention missing fields
        error_details = str(data["detail"])
        assert "patient_id" in error_details or "provider_id" in error_details
    
    def test_create_claim_invalid_patient_id(self, client, mock_auth, sample_provider, sample_health_plan):
        """Test creating a claim with non-existent patient ID."""
        claim_data = {
            "patient_id": 99999,  # Non-existent patient
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "patient" in data["detail"].lower() and "not found" in data["detail"].lower()
    
    def test_create_claim_invalid_provider_id(self, client, mock_auth, sample_patient, sample_health_plan):
        """Test creating a claim with non-existent provider ID."""
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": 99999,  # Non-existent provider
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "provider" in data["detail"].lower() and "not found" in data["detail"].lower()
    
    def test_create_claim_invalid_health_plan_id(self, client, mock_auth, sample_patient, sample_provider):
        """Test creating a claim with non-existent health plan ID."""
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": 99999,  # Non-existent health plan
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "health plan" in data["detail"].lower() and "not found" in data["detail"].lower()
    
    def test_create_claim_invalid_value_format(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test creating a claim with invalid value format."""
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "invalid_value"  # Invalid value
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_claim_negative_value(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test creating a claim with negative value."""
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "-100.00"  # Negative value
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_claim_future_date(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test creating a claim with future date."""
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2050-01-15",  # Future date
            "value": "100.00"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_claim_invalid_status(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test creating a claim with invalid status."""
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00",
            "status": "invalid_status"  # Invalid status
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestClaimRetrieval:
    """Test claim retrieval functionality."""
    
    def test_get_claim_by_id(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test retrieving a claim by ID."""
        # First create a claim
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "150.00",
            "description": "Test claim"
        }
        
        create_response = client.post("/api/claims/", json=claim_data)
        assert create_response.status_code == 201
        created_claim = create_response.json()
        claim_id = created_claim["id"]
        
        # Now retrieve the claim
        response = client.get(f"/api/claims/{claim_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == claim_id
        assert data["patient_id"] == claim_data["patient_id"]
        assert data["procedure_code"] == claim_data["procedure_code"]
    
    def test_get_claim_not_found(self, client, mock_auth):
        """Test retrieving a non-existent claim."""
        response = client.get("/api/claims/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_list_claims(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test listing claims with pagination."""
        # Create multiple claims
        claims_data = [
            {
                "patient_id": sample_patient["id"],
                "provider_id": sample_provider["id"],
                "plan_id": sample_health_plan["id"],
                "procedure_code": "40101019",
                "diagnosis_code": "Z511",
                "date": "2024-01-15",
                "value": f"{100 + i}.00",
                "description": f"Test claim {i+1}"
            }
            for i in range(3)
        ]
        
        for claim_data in claims_data:
            response = client.post("/api/claims/", json=claim_data)
            assert response.status_code == 201
        
        # List claims
        response = client.get("/api/claims/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert len(data["items"]) == 3
        assert data["total"] == 3
    
    def test_list_claims_with_filters(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test listing claims with filters."""
        # Create claims with different statuses
        claims_data = [
            {
                "patient_id": sample_patient["id"],
                "provider_id": sample_provider["id"],
                "plan_id": sample_health_plan["id"],
                "procedure_code": "40101019",
                "diagnosis_code": "Z511",
                "date": "2024-01-15",
                "value": "100.00",
                "status": "pending"
            },
            {
                "patient_id": sample_patient["id"],
                "provider_id": sample_provider["id"],
                "plan_id": sample_health_plan["id"],
                "procedure_code": "40101019",
                "diagnosis_code": "Z511",
                "date": "2024-01-16",
                "value": "200.00",
                "status": "approved"
            }
        ]
        
        for claim_data in claims_data:
            response = client.post("/api/claims/", json=claim_data)
            assert response.status_code == 201
        
        # Filter by status
        response = client.get("/api/claims/?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "pending"
        
        # Filter by patient_id
        response = client.get(f"/api/claims/?patient_id={sample_patient['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(item["patient_id"] == sample_patient["id"] for item in data["items"])


class TestClaimUpdate:
    """Test claim update functionality."""
    
    def test_update_claim_valid_data(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test updating a claim with valid data."""
        # Create a claim first
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00",
            "status": "pending"
        }
        
        create_response = client.post("/api/claims/", json=claim_data)
        assert create_response.status_code == 201
        claim_id = create_response.json()["id"]
        
        # Update the claim
        update_data = {
            "status": "approved",
            "value": "150.00",
            "description": "Updated claim description"
        }
        
        response = client.put(f"/api/claims/{claim_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == update_data["status"]
        assert float(data["value"]) == float(update_data["value"])
        assert data["description"] == update_data["description"]
        assert data["patient_id"] == claim_data["patient_id"]  # Should remain unchanged
    
    def test_update_claim_not_found(self, client, mock_auth):
        """Test updating a non-existent claim."""
        update_data = {
            "status": "approved"
        }
        
        response = client.put("/api/claims/99999", json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestClaimDeletion:
    """Test claim deletion functionality."""
    
    def test_delete_claim(self, client, mock_auth, sample_patient, sample_provider, sample_health_plan):
        """Test deleting a claim."""
        # Create a claim first
        claim_data = {
            "patient_id": sample_patient["id"],
            "provider_id": sample_provider["id"],
            "plan_id": sample_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00"
        }
        
        create_response = client.post("/api/claims/", json=claim_data)
        assert create_response.status_code == 201
        claim_id = create_response.json()["id"]
        
        # Delete the claim
        response = client.delete(f"/api/claims/{claim_id}")
        
        assert response.status_code == 204
        
        # Verify claim is deleted
        get_response = client.get(f"/api/claims/{claim_id}")
        assert get_response.status_code == 404
    
    def test_delete_claim_not_found(self, client, mock_auth):
        """Test deleting a non-existent claim."""
        response = client.delete("/api/claims/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestClaimValidation:
    """Test claim data validation."""
    
    def test_claim_schema_validation(self):
        """Test ClaimCreate schema validation."""
        # Valid data
        valid_data = {
            "patient_id": 1,
            "provider_id": 1,
            "plan_id": 1,
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00"
        }
        
        claim = ClaimCreate(**valid_data)
        assert claim.patient_id == valid_data["patient_id"]
        assert claim.procedure_code == valid_data["procedure_code"]
        assert claim.value == Decimal(valid_data["value"])
    
    def test_claim_schema_validation_invalid_value(self):
        """Test ClaimCreate schema validation with invalid value."""
        invalid_data = {
            "patient_id": 1,
            "provider_id": 1,
            "plan_id": 1,
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "invalid_value"
        }
        
        with pytest.raises(Exception):  # Pydantic validation error
            ClaimCreate(**invalid_data)


class TestClaimAuthentication:
    """Test claim endpoints authentication."""
    
    def test_create_claim_without_auth(self, client):
        """Test creating a claim without authentication."""
        claim_data = {
            "patient_id": 1,
            "provider_id": 1,
            "plan_id": 1,
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_claim_without_auth(self, client):
        """Test getting a claim without authentication."""
        response = client.get("/api/claims/1")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__])