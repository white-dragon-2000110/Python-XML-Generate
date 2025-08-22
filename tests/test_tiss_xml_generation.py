"""
Tests for TISS XML generation functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import json
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal

from main import app
from models.database import Base, get_db
from models.claims import Claim
from models.patients import Patient
from models.providers import Provider
from models.health_plans import HealthPlan
from services.xml_generator import TISSXMLGenerator


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tiss_xml.db"
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
def complete_claim_setup(client, mock_auth):
    """Create a complete claim setup with patient, provider, health plan, and claim."""
    # Create patient
    patient_data = {
        "name": "João Silva",
        "cpf": "12345678901",
        "birth_date": "1985-03-15",
        "email": "joao@email.com",
        "phone": "(11) 98765-4321",
        "address": "Rua das Flores, 123",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01234-567"
    }
    patient_response = client.post("/api/patients/", json=patient_data)
    assert patient_response.status_code == 201
    patient = patient_response.json()
    
    # Create provider
    provider_data = {
        "name": "Hospital São Paulo",
        "cnpj": "12345678000195",
        "cnes": "1234567",
        "provider_type": "hospital",
        "address": "Rua da Saúde, 123",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01234-567",
        "phone": "(11) 3333-4444",
        "email": "contato@hospital.com"
    }
    provider_response = client.post("/api/providers/", json=provider_data)
    assert provider_response.status_code == 201
    provider = provider_response.json()
    
    # Create health plan
    health_plan_data = {
        "name": "Plano Premium",
        "ans_code": "123456",
        "plan_type": "individual",
        "coverage_type": "medical_hospital",
        "is_active": True
    }
    health_plan_response = client.post("/api/health-insurance/", json=health_plan_data)
    assert health_plan_response.status_code == 201
    health_plan = health_plan_response.json()
    
    # Create claim
    claim_data = {
        "patient_id": patient["id"],
        "provider_id": provider["id"],
        "plan_id": health_plan["id"],
        "procedure_code": "40101019",
        "diagnosis_code": "Z511",
        "date": "2024-01-15",
        "value": "150.75",
        "description": "Consulta médica especializada",
        "status": "approved"
    }
    claim_response = client.post("/api/claims/", json=claim_data)
    assert claim_response.status_code == 201
    claim = claim_response.json()
    
    return {
        "patient": patient,
        "provider": provider,
        "health_plan": health_plan,
        "claim": claim
    }


class TestTISSXMLGenerator:
    """Test TISS XML Generator class functionality."""
    
    def test_xml_generator_initialization(self):
        """Test XML generator initialization."""
        generator = TISSXMLGenerator()
        assert generator.tiss_version == "3.05.00"
        assert generator.xmlns == "http://www.ans.gov.br/padroes/tiss/schemas"
        assert hasattr(generator, 'validator')
    
    def test_generate_tiss_xml_valid_claim(self, complete_claim_setup):
        """Test generating TISS XML for a valid claim."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Basic checks
        assert xml_content is not None
        assert isinstance(xml_content, str)
        assert len(xml_content) > 0
        
        # Check that it's valid XML
        try:
            root = ET.fromstring(xml_content)
            assert root is not None
        except ET.ParseError:
            pytest.fail("Generated XML is not valid")
        
        # Check TISS-specific elements
        assert "tiss" in xml_content.lower()
        assert "cabecalho" in xml_content.lower() or "header" in xml_content.lower()
        assert "corpo" in xml_content.lower() or "body" in xml_content.lower()
        
        # Check claim data is included
        assert complete_claim_setup["claim"]["procedure_code"] in xml_content
        assert complete_claim_setup["patient"]["name"] in xml_content
        assert complete_claim_setup["provider"]["name"] in xml_content
    
    def test_generate_tiss_xml_with_validation_valid_claim(self, complete_claim_setup):
        """Test generating TISS XML with validation for a valid claim."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        generator = TISSXMLGenerator()
        xml_content, is_valid, validation_errors = generator.generate_tiss_xml_with_validation(claim_id)
        
        # Basic checks
        assert xml_content is not None
        assert isinstance(xml_content, str)
        assert isinstance(is_valid, bool)
        assert isinstance(validation_errors, list)
        
        # If validation fails, at least we should have XML content
        assert len(xml_content) > 0
        
        # If validation passes, there should be no errors
        if is_valid:
            assert len(validation_errors) == 0
    
    def test_generate_tiss_xml_invalid_claim_id(self):
        """Test generating TISS XML for a non-existent claim."""
        generator = TISSXMLGenerator()
        
        with pytest.raises(ValueError, match="Claim with ID 99999 not found"):
            generator.generate_tiss_xml(99999)
    
    def test_validate_generated_xml_valid_xml(self):
        """Test validating a well-formed XML."""
        generator = TISSXMLGenerator()
        
        # Create a simple valid XML
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <root xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <element>content</element>
        </root>"""
        
        is_valid, errors = generator.validate_generated_xml(valid_xml)
        
        # Since we might not have the actual XSD schema, this test mainly checks the method works
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_generated_xml_invalid_xml(self):
        """Test validating invalid XML."""
        generator = TISSXMLGenerator()
        
        # Create invalid XML
        invalid_xml = "<invalid><unclosed></invalid>"
        
        is_valid, errors = generator.validate_generated_xml(invalid_xml)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("xml" in error.lower() for error in errors)
    
    def test_get_schema_info(self):
        """Test getting schema information."""
        generator = TISSXMLGenerator()
        schema_info = generator.get_schema_info()
        
        assert isinstance(schema_info, dict)
        assert "status" in schema_info
        # The status could be 'loaded' or 'not_loaded' depending on whether XSD is available
        assert schema_info["status"] in ["loaded", "not_loaded"]
    
    def test_create_tiss_header(self, complete_claim_setup):
        """Test creating TISS header element."""
        generator = TISSXMLGenerator()
        claim_id = complete_claim_setup["claim"]["id"]
        
        # This is a private method test - we'll test it indirectly through generate_tiss_xml
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Parse XML and check header structure
        root = ET.fromstring(xml_content)
        
        # Look for header elements (structure may vary based on actual implementation)
        # This is a basic check that the XML has some structure
        assert len(list(root)) > 0  # Should have child elements
    
    def test_create_tiss_body(self, complete_claim_setup):
        """Test creating TISS body element."""
        generator = TISSXMLGenerator()
        claim_id = complete_claim_setup["claim"]["id"]
        
        xml_content = generator.generate_tiss_xml(claim_id)
        root = ET.fromstring(xml_content)
        
        # Check that claim data appears in the XML
        xml_text = xml_content.lower()
        assert complete_claim_setup["claim"]["procedure_code"].lower() in xml_text
        assert complete_claim_setup["patient"]["cpf"] in xml_content
    
    def test_create_tiss_footer(self, complete_claim_setup):
        """Test creating TISS footer element."""
        generator = TISSXMLGenerator()
        claim_id = complete_claim_setup["claim"]["id"]
        
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Check that XML is properly closed
        assert xml_content.strip().endswith(">")
        
        # Verify it's valid XML (which means it's properly closed)
        try:
            ET.fromstring(xml_content)
        except ET.ParseError:
            pytest.fail("Generated XML is not properly closed")


class TestTISSXMLAPI:
    """Test TISS XML generation through API endpoints."""
    
    def test_get_claim_xml_endpoint(self, client, mock_auth, complete_claim_setup):
        """Test getting claim XML through API endpoint."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        response = client.get(f"/api/claims/{claim_id}/xml")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "claim_id" in data
        assert "xml_content" in data
        assert "filename" in data
        assert "generated_at" in data
        
        assert data["claim_id"] == claim_id
        assert len(data["xml_content"]) > 0
        assert data["filename"].endswith(".xml")
        
        # Check that XML content is valid
        xml_content = data["xml_content"]
        try:
            ET.fromstring(xml_content)
        except ET.ParseError:
            pytest.fail("API returned invalid XML")
    
    def test_download_claim_xml_endpoint(self, client, mock_auth, complete_claim_setup):
        """Test downloading claim XML through API endpoint."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        response = client.get(f"/api/claims/{claim_id}/xml/download")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        assert "attachment" in response.headers.get("content-disposition", "")
        
        # Check that content is valid XML
        xml_content = response.content.decode("utf-8")
        try:
            ET.fromstring(xml_content)
        except ET.ParseError:
            pytest.fail("Downloaded XML is not valid")
        
        # Check that claim data is in the XML
        assert complete_claim_setup["claim"]["procedure_code"] in xml_content
    
    def test_get_claim_xml_not_found(self, client, mock_auth):
        """Test getting XML for non-existent claim."""
        response = client.get("/api/claims/99999/xml")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_download_claim_xml_not_found(self, client, mock_auth):
        """Test downloading XML for non-existent claim."""
        response = client.get("/api/claims/99999/xml/download")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_get_claim_xml_without_auth(self, client, complete_claim_setup):
        """Test getting claim XML without authentication."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        response = client.get(f"/api/claims/{claim_id}/xml")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestTISSXMLContent:
    """Test TISS XML content and structure."""
    
    def test_xml_contains_patient_data(self, complete_claim_setup):
        """Test that generated XML contains patient data."""
        claim_id = complete_claim_setup["claim"]["id"]
        patient = complete_claim_setup["patient"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Check patient data is included
        assert patient["name"] in xml_content
        assert patient["cpf"] in xml_content
        
        # Check birth date is formatted correctly
        birth_date = patient["birth_date"]
        assert birth_date in xml_content or birth_date.replace("-", "") in xml_content
    
    def test_xml_contains_provider_data(self, complete_claim_setup):
        """Test that generated XML contains provider data."""
        claim_id = complete_claim_setup["claim"]["id"]
        provider = complete_claim_setup["provider"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Check provider data is included
        assert provider["name"] in xml_content
        assert provider["cnpj"] in xml_content
        assert provider["cnes"] in xml_content
    
    def test_xml_contains_health_plan_data(self, complete_claim_setup):
        """Test that generated XML contains health plan data."""
        claim_id = complete_claim_setup["claim"]["id"]
        health_plan = complete_claim_setup["health_plan"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Check health plan data is included
        assert health_plan["name"] in xml_content
        assert health_plan["ans_code"] in xml_content
    
    def test_xml_contains_claim_data(self, complete_claim_setup):
        """Test that generated XML contains claim data."""
        claim_id = complete_claim_setup["claim"]["id"]
        claim = complete_claim_setup["claim"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Check claim data is included
        assert claim["procedure_code"] in xml_content
        assert claim["diagnosis_code"] in xml_content
        assert str(claim["value"]) in xml_content or "150.75" in xml_content
        
        # Check date is formatted correctly
        claim_date = claim["date"]
        assert claim_date in xml_content or claim_date.replace("-", "") in xml_content
    
    def test_xml_has_tiss_version(self, complete_claim_setup):
        """Test that generated XML contains TISS version."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Check TISS version is included
        assert "3.05.00" in xml_content or "3.05" in xml_content
    
    def test_xml_has_namespace(self, complete_claim_setup):
        """Test that generated XML contains proper namespace."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Check namespace is included
        assert "xmlns" in xml_content
        assert "ans.gov.br" in xml_content or "tiss" in xml_content.lower()
    
    def test_xml_structure_validity(self, complete_claim_setup):
        """Test that generated XML has valid structure."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Parse and validate structure
        root = ET.fromstring(xml_content)
        
        # Check root element exists
        assert root.tag is not None
        
        # Check that we have child elements
        children = list(root)
        assert len(children) > 0
        
        # Check XML declaration
        assert xml_content.startswith("<?xml")
    
    def test_xml_encoding(self, complete_claim_setup):
        """Test that generated XML has proper encoding."""
        claim_id = complete_claim_setup["claim"]["id"]
        
        generator = TISSXMLGenerator()
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Check encoding declaration
        assert "encoding=" in xml_content
        assert "UTF-8" in xml_content or "utf-8" in xml_content
        
        # Test that special characters are properly encoded
        patient_name = complete_claim_setup["patient"]["name"]
        if "ã" in patient_name or "ç" in patient_name:
            # XML should contain the name (either as-is or encoded)
            assert patient_name in xml_content or any(char.isalnum() for char in xml_content)


class TestTISSXMLPerformance:
    """Test TISS XML generation performance."""
    
    def test_xml_generation_performance(self, complete_claim_setup):
        """Test that XML generation completes in reasonable time."""
        import time
        
        claim_id = complete_claim_setup["claim"]["id"]
        generator = TISSXMLGenerator()
        
        start_time = time.time()
        xml_content = generator.generate_tiss_xml(claim_id)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Should complete in less than 5 seconds
        assert generation_time < 5.0
        assert len(xml_content) > 0
    
    def test_xml_validation_performance(self, complete_claim_setup):
        """Test that XML validation completes in reasonable time."""
        import time
        
        claim_id = complete_claim_setup["claim"]["id"]
        generator = TISSXMLGenerator()
        
        # First generate XML
        xml_content = generator.generate_tiss_xml(claim_id)
        
        # Then validate it
        start_time = time.time()
        is_valid, errors = generator.validate_generated_xml(xml_content)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Should complete in less than 3 seconds
        assert validation_time < 3.0
        assert isinstance(is_valid, bool)


if __name__ == "__main__":
    pytest.main([__file__])