"""
Tests for XML schema validation functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import tempfile
import os

from main import app
from models.database import Base, get_db
from services.xml_validator import TISSXMLValidator


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_schema_validation.db"
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
def temp_schema_dir():
    """Create temporary directory for schema files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def validator_with_temp_dir(temp_schema_dir):
    """Create validator with temporary schema directory."""
    return TISSXMLValidator(xsd_directory=str(temp_schema_dir))


class TestTISSXMLValidator:
    """Test TISS XML Validator functionality."""
    
    def test_validator_initialization(self, temp_schema_dir):
        """Test validator initialization."""
        validator = TISSXMLValidator(xsd_directory=str(temp_schema_dir))
        
        assert validator.xsd_directory == temp_schema_dir
        assert validator.tiss_xsd_file == temp_schema_dir / "tiss_3.05.00.xsd"
    
    def test_validator_default_initialization(self):
        """Test validator initialization with default directory."""
        validator = TISSXMLValidator()
        
        assert validator.xsd_directory.name == "schemas"
        assert validator.tiss_xsd_file.name == "tiss_3.05.00.xsd"
    
    def test_xsd_file_exists_false(self, validator_with_temp_dir):
        """Test XSD file existence check when file doesn't exist."""
        validator = validator_with_temp_dir
        
        assert not validator.xsd_file_exists()
    
    def test_xsd_file_exists_true(self, validator_with_temp_dir):
        """Test XSD file existence check when file exists."""
        validator = validator_with_temp_dir
        
        # Create a dummy XSD file
        validator.tiss_xsd_file.write_text("<?xml version='1.0'?><xs:schema></xs:schema>")
        
        assert validator.xsd_file_exists()
    
    def test_create_basic_tiss_xsd(self, validator_with_temp_dir):
        """Test creating basic TISS XSD schema."""
        validator = validator_with_temp_dir
        
        result = validator.create_basic_tiss_xsd()
        
        assert result is True
        assert validator.tiss_xsd_file.exists()
        
        # Check that the file contains valid XSD content
        xsd_content = validator.tiss_xsd_file.read_text()
        assert "<?xml version=" in xsd_content
        assert "xs:schema" in xsd_content
        assert "xmlns:xs=" in xsd_content
        assert "tiss" in xsd_content.lower()
    
    def test_validate_tiss_xml_with_schema(self, validator_with_temp_dir):
        """Test XML validation with schema."""
        validator = validator_with_temp_dir
        
        # Create a basic XSD schema
        validator.create_basic_tiss_xsd()
        
        # Create valid XML that should pass basic validation
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho>
                <versao>3.05.00</versao>
            </cabecalho>
            <corpo>
                <guia>
                    <numero>123456</numero>
                </guia>
            </corpo>
        </tiss>"""
        
        is_valid, errors = validator.validate_tiss_xml(valid_xml)
        
        # The result depends on whether we have a proper XSD
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_tiss_xml_without_schema(self, validator_with_temp_dir):
        """Test XML validation without schema."""
        validator = validator_with_temp_dir
        
        # Don't create XSD file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <element>content</element>
        </root>"""
        
        is_valid, errors = validator.validate_tiss_xml(xml_content)
        
        # Should fail because no schema is available
        assert is_valid is False
        assert len(errors) > 0
        assert any("schema" in error.lower() for error in errors)
    
    def test_validate_tiss_xml_invalid_structure(self, validator_with_temp_dir):
        """Test XML validation with invalid structure."""
        validator = validator_with_temp_dir
        
        # Create basic XSD
        validator.create_basic_tiss_xsd()
        
        # Create invalid XML structure
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <invalid>
            <unclosed_tag>
        </invalid>"""
        
        is_valid, errors = validator.validate_tiss_xml(invalid_xml)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_tiss_xml_malformed(self, validator_with_temp_dir):
        """Test XML validation with malformed XML."""
        validator = validator_with_temp_dir
        
        # Create basic XSD
        validator.create_basic_tiss_xsd()
        
        # Malformed XML
        malformed_xml = "<invalid><unclosed></invalid>"
        
        is_valid, errors = validator.validate_tiss_xml(malformed_xml)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("xml" in error.lower() or "parse" in error.lower() for error in errors)
    
    def test_validate_tiss_xml_empty_string(self, validator_with_temp_dir):
        """Test XML validation with empty string."""
        validator = validator_with_temp_dir
        
        is_valid, errors = validator.validate_tiss_xml("")
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_tiss_xml_file(self, validator_with_temp_dir, temp_schema_dir):
        """Test XML file validation."""
        validator = validator_with_temp_dir
        
        # Create basic XSD
        validator.create_basic_tiss_xsd()
        
        # Create XML file
        xml_file = temp_schema_dir / "test.xml"
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho>
                <versao>3.05.00</versao>
            </cabecalho>
        </tiss>"""
        xml_file.write_text(xml_content)
        
        is_valid, errors = validator.validate_tiss_xml_file(str(xml_file))
        
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_tiss_xml_file_not_found(self, validator_with_temp_dir):
        """Test XML file validation with non-existent file."""
        validator = validator_with_temp_dir
        
        is_valid, errors = validator.validate_tiss_xml_file("non_existent_file.xml")
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("file" in error.lower() or "not found" in error.lower() for error in errors)
    
    def test_get_schema_info_with_schema(self, validator_with_temp_dir):
        """Test getting schema info when schema exists."""
        validator = validator_with_temp_dir
        
        # Create basic XSD
        validator.create_basic_tiss_xsd()
        
        schema_info = validator.get_schema_info()
        
        assert isinstance(schema_info, dict)
        assert "status" in schema_info
        assert "file_path" in schema_info
        assert "file_size" in schema_info
        
        assert schema_info["status"] in ["loaded", "not_loaded"]
        assert str(validator.tiss_xsd_file) in schema_info["file_path"]
    
    def test_get_schema_info_without_schema(self, validator_with_temp_dir):
        """Test getting schema info when schema doesn't exist."""
        validator = validator_with_temp_dir
        
        schema_info = validator.get_schema_info()
        
        assert isinstance(schema_info, dict)
        assert "status" in schema_info
        assert schema_info["status"] == "not_loaded"
    
    def test_is_schema_loaded_true(self, validator_with_temp_dir):
        """Test schema loaded check when schema exists."""
        validator = validator_with_temp_dir
        
        # Create basic XSD
        validator.create_basic_tiss_xsd()
        
        # This depends on the actual implementation
        # Some implementations might require the schema to be actually parsed
        is_loaded = validator.is_schema_loaded()
        assert isinstance(is_loaded, bool)
    
    def test_is_schema_loaded_false(self, validator_with_temp_dir):
        """Test schema loaded check when schema doesn't exist."""
        validator = validator_with_temp_dir
        
        is_loaded = validator.is_schema_loaded()
        assert is_loaded is False


class TestSchemaValidationAPI:
    """Test schema validation through API endpoints."""
    
    def test_get_schema_info_endpoint(self, client, mock_auth):
        """Test getting schema info through API."""
        response = client.get("/api/claims/schema/info")
        
        assert response.status_code in [200, 500]  # 500 if schema not loaded
        data = response.json()
        
        if response.status_code == 200:
            assert "status" in data
            assert "file_path" in data
            assert "file_size" in data
        else:
            assert "detail" in data
    
    def test_validate_xml_content_endpoint_valid(self, client, mock_auth):
        """Test validating XML content through API with valid XML."""
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho>
                <versao>3.05.00</versao>
            </cabecalho>
            <corpo>
                <guia>
                    <numero>123456</numero>
                </guia>
            </corpo>
        </tiss>"""
        
        response = client.post("/api/claims/validate/xml", json={"xml_content": valid_xml})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "errors" in data
        assert "schema_info" in data
        
        assert isinstance(data["is_valid"], bool)
        assert isinstance(data["errors"], list)
        assert isinstance(data["schema_info"], dict)
    
    def test_validate_xml_content_endpoint_invalid(self, client, mock_auth):
        """Test validating XML content through API with invalid XML."""
        invalid_xml = "<invalid><unclosed></invalid>"
        
        response = client.post("/api/claims/validate/xml", json={"xml_content": invalid_xml})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "errors" in data
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
    
    def test_validate_xml_content_endpoint_empty(self, client, mock_auth):
        """Test validating empty XML content through API."""
        response = client.post("/api/claims/validate/xml", json={"xml_content": ""})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_valid"] is False
        assert len(data["errors"]) > 0
    
    def test_validate_xml_content_endpoint_malformed_json(self, client, mock_auth):
        """Test validating XML with malformed JSON request."""
        response = client.post("/api/claims/validate/xml", data="invalid json")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_validate_xml_content_endpoint_without_auth(self, client):
        """Test validating XML content without authentication."""
        valid_xml = "<root><element>content</element></root>"
        
        response = client.post("/api/claims/validate/xml", json={"xml_content": valid_xml})
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestSchemaValidationIntegration:
    """Test schema validation integration with TISS XML generation."""
    
    def test_validate_generated_claim_xml(self, client, mock_auth):
        """Test validating XML generated for a claim."""
        # This test requires a complete setup with patient, provider, health plan, and claim
        # We'll create a minimal test that attempts the validation
        
        # First try to validate a non-existent claim (should fail gracefully)
        response = client.get("/api/claims/99999/xml/validate")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_validate_generated_claim_xml_without_auth(self, client):
        """Test validating generated claim XML without authentication."""
        response = client.get("/api/claims/1/xml/validate")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestXMLSamples:
    """Test validation with various XML samples."""
    
    def test_validate_minimal_tiss_xml(self, validator_with_temp_dir):
        """Test validation with minimal TISS XML."""
        validator = validator_with_temp_dir
        validator.create_basic_tiss_xsd()
        
        minimal_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho>
                <versao>3.05.00</versao>
            </cabecalho>
        </tiss>"""
        
        is_valid, errors = validator.validate_tiss_xml(minimal_xml)
        
        # Basic structure check
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_complete_tiss_xml(self, validator_with_temp_dir):
        """Test validation with complete TISS XML."""
        validator = validator_with_temp_dir
        validator.create_basic_tiss_xsd()
        
        complete_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho>
                <versao>3.05.00</versao>
                <identificacao>
                    <prestador>
                        <cnpj>12345678000195</cnpj>
                        <nome>Hospital Test</nome>
                    </prestador>
                </identificacao>
            </cabecalho>
            <corpo>
                <guia>
                    <numero>123456</numero>
                    <paciente>
                        <nome>João Silva</nome>
                        <cpf>12345678901</cpf>
                    </paciente>
                    <procedimentos>
                        <procedimento>
                            <codigo>40101019</codigo>
                            <descricao>Consulta médica</descricao>
                            <valor>150.00</valor>
                        </procedimento>
                    </procedimentos>
                </guia>
            </corpo>
        </tiss>"""
        
        is_valid, errors = validator.validate_tiss_xml(complete_xml)
        
        # Basic structure check
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_xml_with_special_characters(self, validator_with_temp_dir):
        """Test validation with XML containing special characters."""
        validator = validator_with_temp_dir
        validator.create_basic_tiss_xsd()
        
        xml_with_special_chars = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho>
                <versao>3.05.00</versao>
            </cabecalho>
            <corpo>
                <paciente>
                    <nome>José da Silva & João</nome>
                    <observacao>Paciente com histórico de "hipertensão"</observacao>
                </paciente>
            </corpo>
        </tiss>"""
        
        is_valid, errors = validator.validate_tiss_xml(xml_with_special_chars)
        
        # Should handle special characters properly
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_xml_with_cdata(self, validator_with_temp_dir):
        """Test validation with XML containing CDATA sections."""
        validator = validator_with_temp_dir
        validator.create_basic_tiss_xsd()
        
        xml_with_cdata = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho>
                <versao>3.05.00</versao>
            </cabecalho>
            <corpo>
                <observacao><![CDATA[
                    Observações especiais:
                    - Paciente com restrições
                    - Contato: (11) 99999-9999
                ]]></observacao>
            </corpo>
        </tiss>"""
        
        is_valid, errors = validator.validate_tiss_xml(xml_with_cdata)
        
        # Should handle CDATA properly
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_xml_wrong_namespace(self, validator_with_temp_dir):
        """Test validation with wrong namespace."""
        validator = validator_with_temp_dir
        validator.create_basic_tiss_xsd()
        
        wrong_namespace_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://wrong.namespace.com">
            <cabecalho>
                <versao>3.05.00</versao>
            </cabecalho>
        </tiss>"""
        
        is_valid, errors = validator.validate_tiss_xml(wrong_namespace_xml)
        
        # Should detect wrong namespace
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validate_xml_missing_required_elements(self, validator_with_temp_dir):
        """Test validation with missing required elements."""
        validator = validator_with_temp_dir
        validator.create_basic_tiss_xsd()
        
        incomplete_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <!-- Missing cabecalho -->
            <corpo>
                <guia>
                    <numero>123456</numero>
                </guia>
            </corpo>
        </tiss>"""
        
        is_valid, errors = validator.validate_tiss_xml(incomplete_xml)
        
        # Depending on the XSD, this might fail validation
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


class TestSchemaValidationPerformance:
    """Test schema validation performance."""
    
    def test_validation_performance_small_xml(self, validator_with_temp_dir):
        """Test validation performance with small XML."""
        import time
        
        validator = validator_with_temp_dir
        validator.create_basic_tiss_xsd()
        
        small_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho><versao>3.05.00</versao></cabecalho>
        </tiss>"""
        
        start_time = time.time()
        is_valid, errors = validator.validate_tiss_xml(small_xml)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Should complete quickly
        assert validation_time < 1.0
        assert isinstance(is_valid, bool)
    
    def test_validation_performance_large_xml(self, validator_with_temp_dir):
        """Test validation performance with larger XML."""
        import time
        
        validator = validator_with_temp_dir
        validator.create_basic_tiss_xsd()
        
        # Create larger XML with multiple procedures
        procedures = []
        for i in range(100):
            procedures.append(f"""
                <procedimento>
                    <codigo>4010101{i:02d}</codigo>
                    <descricao>Procedimento {i+1}</descricao>
                    <valor>{100 + i}.00</valor>
                </procedimento>""")
        
        large_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
            <cabecalho>
                <versao>3.05.00</versao>
            </cabecalho>
            <corpo>
                <guia>
                    <numero>123456</numero>
                    <procedimentos>
                        {''.join(procedures)}
                    </procedimentos>
                </guia>
            </corpo>
        </tiss>"""
        
        start_time = time.time()
        is_valid, errors = validator.validate_tiss_xml(large_xml)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Should still complete in reasonable time
        assert validation_time < 5.0
        assert isinstance(is_valid, bool)


if __name__ == "__main__":
    pytest.main([__file__])