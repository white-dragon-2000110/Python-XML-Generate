"""
Tests for invalid data handling across all endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import json
from datetime import date, datetime

from main import app
from models.database import Base, get_db


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_invalid_data.db"
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


class TestInvalidJSONHandling:
    """Test handling of invalid JSON data."""
    
    def test_malformed_json_patient_creation(self, client, mock_auth):
        """Test patient creation with malformed JSON."""
        malformed_json = '{"name": "Test", "cpf":'  # Incomplete JSON
        
        response = client.post(
            "/api/patients/",
            data=malformed_json,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_malformed_json_claim_creation(self, client, mock_auth):
        """Test claim creation with malformed JSON."""
        malformed_json = '{"patient_id": 1, "provider_id"'  # Incomplete JSON
        
        response = client.post(
            "/api/claims/",
            data=malformed_json,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_invalid_content_type(self, client, mock_auth):
        """Test endpoints with invalid content type."""
        valid_data = {"name": "Test Patient", "cpf": "12345678901", "birth_date": "1990-01-01"}
        
        response = client.post(
            "/api/patients/",
            data=json.dumps(valid_data),
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_empty_json_body(self, client, mock_auth):
        """Test endpoints with empty JSON body."""
        response = client.post(
            "/api/patients/",
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_null_json_body(self, client, mock_auth):
        """Test endpoints with null JSON body."""
        response = client.post(
            "/api/patients/",
            data="null",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestInvalidDataTypes:
    """Test handling of invalid data types."""
    
    def test_string_instead_of_integer_patient_id(self, client, mock_auth):
        """Test using string instead of integer for patient ID."""
        response = client.get("/api/patients/not_a_number")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_string_instead_of_integer_claim_id(self, client, mock_auth):
        """Test using string instead of integer for claim ID."""
        response = client.get("/api/claims/not_a_number")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_invalid_date_format_patient(self, client, mock_auth):
        """Test patient creation with invalid date format."""
        patient_data = {
            "name": "Test Patient",
            "cpf": "12345678901",
            "birth_date": "invalid-date"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Check that the error mentions date validation
        error_str = str(data["detail"]).lower()
        assert "date" in error_str or "format" in error_str
    
    def test_invalid_decimal_format_claim(self, client, mock_auth):
        """Test claim creation with invalid decimal format."""
        claim_data = {
            "patient_id": 1,
            "provider_id": 1,
            "plan_id": 1,
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "not_a_number"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_boolean_as_string(self, client, mock_auth):
        """Test health plan creation with boolean as string."""
        health_plan_data = {
            "name": "Test Plan",
            "ans_code": "123456",
            "plan_type": "individual",
            "coverage_type": "medical_hospital",
            "is_active": "true"  # Should be boolean, not string
        }
        
        response = client.post("/api/health-insurance/", json=health_plan_data)
        
        # This might pass or fail depending on Pydantic settings
        # We test that it either succeeds or gives appropriate error
        if response.status_code != 201:
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
    
    def test_negative_integer_ids(self, client, mock_auth):
        """Test endpoints with negative integer IDs."""
        response = client.get("/api/patients/-1")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_zero_as_id(self, client, mock_auth):
        """Test endpoints with zero as ID."""
        response = client.get("/api/patients/0")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_float_as_integer_id(self, client, mock_auth):
        """Test endpoints with float as integer ID."""
        response = client.get("/api/patients/1.5")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestInvalidFieldValues:
    """Test handling of invalid field values."""
    
    def test_empty_required_strings(self, client, mock_auth):
        """Test creation with empty required string fields."""
        patient_data = {
            "name": "",  # Empty name
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_whitespace_only_strings(self, client, mock_auth):
        """Test creation with whitespace-only string fields."""
        patient_data = {
            "name": "   ",  # Whitespace only
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_invalid_email_formats(self, client, mock_auth):
        """Test patient creation with various invalid email formats."""
        invalid_emails = [
            "invalid",
            "@domain.com",
            "user@",
            "user@domain",
            "user.domain.com",
            "user@domain.",
            "user space@domain.com",
            "user@domain space.com"
        ]
        
        for invalid_email in invalid_emails:
            patient_data = {
                "name": "Test Patient",
                "cpf": "12345678901",
                "birth_date": "1990-01-01",
                "email": invalid_email
            }
            
            response = client.post("/api/patients/", json=patient_data)
            
            assert response.status_code == 422, f"Email '{invalid_email}' should be invalid"
            data = response.json()
            assert "detail" in data
    
    def test_invalid_phone_formats(self, client, mock_auth):
        """Test patient creation with invalid phone formats."""
        invalid_phones = [
            "123",  # Too short
            "abc-def-ghij",  # Letters
            "123-456-78901234567890",  # Too long
        ]
        
        for invalid_phone in invalid_phones:
            patient_data = {
                "name": "Test Patient",
                "cpf": "12345678901",
                "birth_date": "1990-01-01",
                "phone": invalid_phone
            }
            
            response = client.post("/api/patients/", json=patient_data)
            
            # Phone validation might be lenient, so we check if it fails
            if response.status_code != 201:
                assert response.status_code == 422
                data = response.json()
                assert "detail" in data
    
    def test_invalid_cpf_formats(self, client, mock_auth):
        """Test patient creation with invalid CPF formats."""
        invalid_cpfs = [
            "123",  # Too short
            "12345678901234567890",  # Too long
            "abcdefghijk",  # Letters
            "123.456.789-01",  # With formatting (might be valid depending on validation)
            "",  # Empty
            "00000000000",  # All zeros
            "11111111111"  # All same digit
        ]
        
        for invalid_cpf in invalid_cpfs:
            patient_data = {
                "name": "Test Patient",
                "cpf": invalid_cpf,
                "birth_date": "1990-01-01"
            }
            
            response = client.post("/api/patients/", json=patient_data)
            
            assert response.status_code == 422, f"CPF '{invalid_cpf}' should be invalid"
            data = response.json()
            assert "detail" in data
    
    def test_future_birth_dates(self, client, mock_auth):
        """Test patient creation with future birth dates."""
        future_dates = [
            "2050-01-01",
            "2030-12-31",
            (datetime.now().date().replace(year=datetime.now().year + 1)).isoformat()
        ]
        
        for future_date in future_dates:
            patient_data = {
                "name": "Test Patient",
                "cpf": "12345678901",
                "birth_date": future_date
            }
            
            response = client.post("/api/patients/", json=patient_data)
            
            assert response.status_code == 422, f"Birth date '{future_date}' should be invalid"
            data = response.json()
            assert "detail" in data
    
    def test_invalid_status_values(self, client, mock_auth):
        """Test claim creation with invalid status values."""
        # First create required dependencies (simplified for this test)
        patient_data = {"name": "Test", "cpf": "12345678901", "birth_date": "1990-01-01"}
        patient_response = client.post("/api/patients/", json=patient_data)
        patient_id = patient_response.json()["id"] if patient_response.status_code == 201 else 1
        
        invalid_statuses = [
            "invalid_status",
            "PENDING",  # Wrong case
            "pending_approval",  # Doesn't exist
            123,  # Number instead of string
            True  # Boolean instead of string
        ]
        
        for invalid_status in invalid_statuses:
            claim_data = {
                "patient_id": patient_id,
                "provider_id": 1,  # Might not exist, but testing status validation
                "plan_id": 1,
                "procedure_code": "40101019",
                "diagnosis_code": "Z511",
                "date": "2024-01-15",
                "value": "100.00",
                "status": invalid_status
            }
            
            response = client.post("/api/claims/", json=claim_data)
            
            # Might fail due to missing provider/plan, but should mention status if that's the issue
            assert response.status_code in [400, 422]
            data = response.json()
            assert "detail" in data


class TestExtremeValues:
    """Test handling of extreme values."""
    
    def test_very_long_strings(self, client, mock_auth):
        """Test creation with extremely long string values."""
        very_long_string = "A" * 10000
        
        patient_data = {
            "name": very_long_string,
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_very_large_numbers(self, client, mock_auth):
        """Test claim creation with very large numbers."""
        claim_data = {
            "patient_id": 999999999999999999999,  # Very large number
            "provider_id": 1,
            "plan_id": 1,
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "999999999999.99"
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        # Should fail, either due to validation or missing entities
        assert response.status_code in [400, 422]
        data = response.json()
        assert "detail" in data
    
    def test_negative_values_where_not_allowed(self, client, mock_auth):
        """Test claim creation with negative values where not allowed."""
        claim_data = {
            "patient_id": 1,
            "provider_id": 1,
            "plan_id": 1,
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "-100.00"  # Negative value
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_zero_values_where_not_allowed(self, client, mock_auth):
        """Test claim creation with zero values where not allowed."""
        claim_data = {
            "patient_id": 1,
            "provider_id": 1,
            "plan_id": 1,
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "0.00"  # Zero value
        }
        
        response = client.post("/api/claims/", json=claim_data)
        
        # Zero might be allowed or not, depends on business rules
        if response.status_code != 201:
            assert response.status_code in [400, 422]
            data = response.json()
            assert "detail" in data


class TestSpecialCharacters:
    """Test handling of special characters."""
    
    def test_special_characters_in_names(self, client, mock_auth):
        """Test patient creation with special characters in names."""
        special_names = [
            "José da Silva",  # Accented characters
            "Mary O'Connor",  # Apostrophe
            "Jean-Pierre",  # Hyphen
            "王小明",  # Chinese characters
            "José María",  # Multiple accents
            "Smith & Jones",  # Ampersand
            'Jane "Doe"',  # Quotes
        ]
        
        for special_name in special_names:
            patient_data = {
                "name": special_name,
                "cpf": f"{str(hash(special_name))[-11:]}".zfill(11),
                "birth_date": "1990-01-01"
            }
            
            response = client.post("/api/patients/", json=patient_data)
            
            # Should either succeed or give appropriate validation error
            if response.status_code != 201:
                # If it fails, check it's due to validation, not a crash
                assert response.status_code == 422
                data = response.json()
                assert "detail" in data
    
    def test_sql_injection_attempts(self, client, mock_auth):
        """Test endpoints with SQL injection attempts."""
        sql_injection_attempts = [
            "'; DROP TABLE patients; --",
            "1' OR '1'='1",
            "admin'; DELETE FROM patients WHERE '1'='1",
            "1'; INSERT INTO patients (name) VALUES ('hacked'); --"
        ]
        
        for injection_attempt in sql_injection_attempts:
            patient_data = {
                "name": injection_attempt,
                "cpf": "12345678901",
                "birth_date": "1990-01-01"
            }
            
            response = client.post("/api/patients/", json=patient_data)
            
            # Should either succeed (treating as normal string) or fail validation
            # But should not cause a server error
            assert response.status_code in [201, 422]
            if response.status_code != 201:
                data = response.json()
                assert "detail" in data
    
    def test_unicode_characters(self, client, mock_auth):
        """Test handling of various Unicode characters."""
        unicode_strings = [
            "🚀 Rocket Patient",  # Emoji
            "Patient № 1",  # Special symbols
            "Müller",  # Umlaut
            "Ñoño",  # Spanish ñ
            "Владимир",  # Cyrillic
            "山田太郎",  # Japanese
        ]
        
        for unicode_string in unicode_strings:
            patient_data = {
                "name": unicode_string,
                "cpf": f"{str(abs(hash(unicode_string)))[-11:]}".zfill(11),
                "birth_date": "1990-01-01"
            }
            
            response = client.post("/api/patients/", json=patient_data)
            
            # Should handle Unicode properly
            if response.status_code != 201:
                assert response.status_code == 422
                data = response.json()
                assert "detail" in data


class TestMissingFields:
    """Test handling of missing required fields."""
    
    def test_missing_all_fields_patient(self, client, mock_auth):
        """Test patient creation with no fields."""
        response = client.post("/api/patients/", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # Should mention missing required fields
        error_str = str(data["detail"]).lower()
        assert "required" in error_str or "missing" in error_str
    
    def test_missing_all_fields_claim(self, client, mock_auth):
        """Test claim creation with no fields."""
        response = client.post("/api/claims/", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_partial_required_fields_patient(self, client, mock_auth):
        """Test patient creation with only some required fields."""
        partial_data = {
            "name": "Test Patient"
            # Missing cpf and birth_date
        }
        
        response = client.post("/api/patients/", json=partial_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_partial_required_fields_claim(self, client, mock_auth):
        """Test claim creation with only some required fields."""
        partial_data = {
            "patient_id": 1,
            "procedure_code": "40101019"
            # Missing other required fields
        }
        
        response = client.post("/api/claims/", json=partial_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestNullValues:
    """Test handling of null values."""
    
    def test_null_required_fields_patient(self, client, mock_auth):
        """Test patient creation with null required fields."""
        patient_data = {
            "name": None,
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_null_optional_fields_patient(self, client, mock_auth):
        """Test patient creation with null optional fields."""
        patient_data = {
            "name": "Test Patient",
            "cpf": "12345678901",
            "birth_date": "1990-01-01",
            "email": None,
            "phone": None
        }
        
        response = client.post("/api/patients/", json=patient_data)
        
        # Should succeed with null optional fields
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == patient_data["name"]
        assert data["email"] is None
        assert data["phone"] is None


class TestConcurrencyAndRaceConditions:
    """Test handling of concurrency issues."""
    
    def test_duplicate_creation_race_condition(self, client, mock_auth):
        """Test creation of duplicate entities in rapid succession."""
        patient_data = {
            "name": "Race Condition Patient",
            "cpf": "12345678901",
            "birth_date": "1990-01-01"
        }
        
        # Try to create the same patient multiple times rapidly
        responses = []
        for _ in range(3):
            response = client.post("/api/patients/", json=patient_data)
            responses.append(response)
        
        # First should succeed, others should fail due to duplicate CPF
        success_count = sum(1 for r in responses if r.status_code == 201)
        failure_count = sum(1 for r in responses if r.status_code in [409, 422])
        
        assert success_count == 1  # Only one should succeed
        assert failure_count >= 1  # Others should fail


class TestErrorResponseFormat:
    """Test that error responses follow consistent format."""
    
    def test_validation_error_format(self, client, mock_auth):
        """Test that validation errors follow consistent format."""
        invalid_data = {
            "name": "",  # Invalid
            "cpf": "invalid",  # Invalid
            "birth_date": "invalid-date"  # Invalid
        }
        
        response = client.post("/api/patients/", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        
        # Check error response structure
        assert "detail" in data
        assert isinstance(data["detail"], (str, list, dict))
        
        # If it's a list (multiple validation errors), check structure
        if isinstance(data["detail"], list):
            for error in data["detail"]:
                assert isinstance(error, dict)
                # Common fields in validation errors
                expected_fields = ["loc", "msg", "type"]
                assert any(field in error for field in expected_fields)
    
    def test_not_found_error_format(self, client, mock_auth):
        """Test that not found errors follow consistent format."""
        response = client.get("/api/patients/99999")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert "not found" in data["detail"].lower()
    
    def test_authentication_error_format(self, client):
        """Test that authentication errors follow consistent format."""
        response = client.get("/api/patients/1")
        
        assert response.status_code == 401
        data = response.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], str)


if __name__ == "__main__":
    pytest.main([__file__])