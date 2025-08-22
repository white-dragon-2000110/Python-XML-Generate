"""
Pytest configuration and shared fixtures for all tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path
import os
from datetime import date, datetime
from decimal import Decimal

from main import app
from models.database import Base, get_db
from models.patients import Patient
from models.providers import Provider
from models.health_plans import HealthPlan
from models.claims import Claim


# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_database.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine for the session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db(test_engine, test_session_factory):
    """Create test database session."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = test_session_factory()
    
    try:
        yield session
    finally:
        session.close()
        # Clean up tables
        Base.metadata.drop_all(bind=test_engine)


def override_get_db(test_db):
    """Override database dependency for testing."""
    try:
        yield test_db
    finally:
        pass


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override."""
    app.dependency_overrides[get_db] = lambda: override_get_db(test_db)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up override
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def mock_auth():
    """Mock authentication for testing."""
    with patch('middleware.auth.auth_middleware') as mock_auth:
        mock_auth.authenticate.return_value = {
            "authenticated": True,
            "api_key": "test-api-key",
            "client_ip": "127.0.0.1",
            "timestamp": datetime.now().isoformat(),
            "rate_limit_remaining": 95
        }
        yield mock_auth


@pytest.fixture
def temp_directory():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# Sample data fixtures
@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing."""
    return {
        "name": "João Silva",
        "cpf": "12345678901",
        "birth_date": "1985-03-15",
        "email": "joao.silva@email.com",
        "phone": "(11) 98765-4321",
        "address": "Rua das Flores, 123",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01234-567"
    }


@pytest.fixture
def sample_provider_data():
    """Sample provider data for testing."""
    return {
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


@pytest.fixture
def sample_health_plan_data():
    """Sample health plan data for testing."""
    return {
        "name": "Plano Premium",
        "ans_code": "123456",
        "plan_type": "individual",
        "coverage_type": "medical_hospital",
        "is_active": True
    }


@pytest.fixture
def sample_claim_data():
    """Sample claim data for testing (requires IDs to be filled)."""
    return {
        "procedure_code": "40101019",
        "diagnosis_code": "Z511",
        "date": "2024-01-15",
        "value": "150.75",
        "description": "Consulta médica especializada",
        "status": "approved"
    }


# Database entity fixtures
@pytest.fixture
def db_patient(test_db, sample_patient_data):
    """Create a patient in the database."""
    patient = Patient(**sample_patient_data)
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture
def db_provider(test_db, sample_provider_data):
    """Create a provider in the database."""
    provider = Provider(**sample_provider_data)
    test_db.add(provider)
    test_db.commit()
    test_db.refresh(provider)
    return provider


@pytest.fixture
def db_health_plan(test_db, sample_health_plan_data):
    """Create a health plan in the database."""
    health_plan = HealthPlan(**sample_health_plan_data)
    test_db.add(health_plan)
    test_db.commit()
    test_db.refresh(health_plan)
    return health_plan


@pytest.fixture
def db_claim(test_db, db_patient, db_provider, db_health_plan, sample_claim_data):
    """Create a claim in the database."""
    claim_data = sample_claim_data.copy()
    claim_data.update({
        "patient_id": db_patient.id,
        "provider_id": db_provider.id,
        "plan_id": db_health_plan.id
    })
    
    claim = Claim(**claim_data)
    test_db.add(claim)
    test_db.commit()
    test_db.refresh(claim)
    return claim


# API fixtures
@pytest.fixture
def api_patient(client, mock_auth, sample_patient_data):
    """Create a patient through the API."""
    response = client.post("/api/patients/", json=sample_patient_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def api_provider(client, mock_auth, sample_provider_data):
    """Create a provider through the API."""
    response = client.post("/api/providers/", json=sample_provider_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def api_health_plan(client, mock_auth, sample_health_plan_data):
    """Create a health plan through the API."""
    response = client.post("/api/health-insurance/", json=sample_health_plan_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def api_claim(client, mock_auth, api_patient, api_provider, api_health_plan, sample_claim_data):
    """Create a claim through the API."""
    claim_data = sample_claim_data.copy()
    claim_data.update({
        "patient_id": api_patient["id"],
        "provider_id": api_provider["id"],
        "plan_id": api_health_plan["id"]
    })
    
    response = client.post("/api/claims/", json=claim_data)
    assert response.status_code == 201
    return response.json()


# Complex setup fixtures
@pytest.fixture
def complete_setup(api_patient, api_provider, api_health_plan, api_claim):
    """Complete setup with all entities created through API."""
    return {
        "patient": api_patient,
        "provider": api_provider,
        "health_plan": api_health_plan,
        "claim": api_claim
    }


@pytest.fixture
def multiple_patients(client, mock_auth):
    """Create multiple patients for testing pagination and filtering."""
    patients_data = [
        {
            "name": "João Silva",
            "cpf": "11111111111",
            "birth_date": "1985-03-15",
            "email": "joao@email.com",
            "city": "São Paulo",
            "state": "SP"
        },
        {
            "name": "Maria Santos",
            "cpf": "22222222222",
            "birth_date": "1990-07-22",
            "email": "maria@email.com",
            "city": "Rio de Janeiro",
            "state": "RJ"
        },
        {
            "name": "Pedro Costa",
            "cpf": "33333333333",
            "birth_date": "1995-12-10",
            "email": "pedro@email.com",
            "city": "Belo Horizonte",
            "state": "MG"
        }
    ]
    
    created_patients = []
    for patient_data in patients_data:
        response = client.post("/api/patients/", json=patient_data)
        assert response.status_code == 201
        created_patients.append(response.json())
    
    return created_patients


@pytest.fixture
def multiple_claims(client, mock_auth, api_patient, api_provider, api_health_plan):
    """Create multiple claims for testing pagination and filtering."""
    claims_data = [
        {
            "patient_id": api_patient["id"],
            "provider_id": api_provider["id"],
            "plan_id": api_health_plan["id"],
            "procedure_code": "40101019",
            "diagnosis_code": "Z511",
            "date": "2024-01-15",
            "value": "100.00",
            "description": "Consulta médica",
            "status": "pending"
        },
        {
            "patient_id": api_patient["id"],
            "provider_id": api_provider["id"],
            "plan_id": api_health_plan["id"],
            "procedure_code": "40101020",
            "diagnosis_code": "Z512",
            "date": "2024-01-16",
            "value": "150.00",
            "description": "Exame laboratorial",
            "status": "approved"
        },
        {
            "patient_id": api_patient["id"],
            "provider_id": api_provider["id"],
            "plan_id": api_health_plan["id"],
            "procedure_code": "40101021",
            "diagnosis_code": "Z513",
            "date": "2024-01-17",
            "value": "200.00",
            "description": "Procedimento cirúrgico",
            "status": "rejected"
        }
    ]
    
    created_claims = []
    for claim_data in claims_data:
        response = client.post("/api/claims/", json=claim_data)
        assert response.status_code == 201
        created_claims.append(response.json())
    
    return created_claims


# XML and validation fixtures
@pytest.fixture
def sample_valid_xml():
    """Sample valid TISS XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <tiss xmlns="http://www.ans.gov.br/padroes/tiss/schemas">
        <cabecalho>
            <versao>3.05.00</versao>
            <identificacao>
                <prestador>
                    <cnpj>12345678000195</cnpj>
                    <nome>Hospital São Paulo</nome>
                </prestador>
            </identificacao>
        </cabecalho>
        <corpo>
            <guia>
                <numero>123456</numero>
                <paciente>
                    <nome>João Silva</nome>
                    <cpf>12345678901</cpf>
                    <dataNascimento>1985-03-15</dataNascimento>
                </paciente>
                <procedimentos>
                    <procedimento>
                        <codigo>40101019</codigo>
                        <descricao>Consulta médica</descricao>
                        <valor>150.75</valor>
                        <data>2024-01-15</data>
                    </procedimento>
                </procedimentos>
            </guia>
        </corpo>
    </tiss>"""


@pytest.fixture
def sample_invalid_xml():
    """Sample invalid XML for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <invalid>
        <unclosed_tag>
            <content>Invalid XML structure</content>
        <!-- Missing closing tag -->
    </invalid>"""


@pytest.fixture
def sample_malformed_xml():
    """Sample malformed XML for testing."""
    return "<invalid><unclosed></invalid>"


# Mock fixtures for external dependencies
@pytest.fixture
def mock_xml_validator():
    """Mock XML validator for testing."""
    with patch('services.xml_validator.TISSXMLValidator') as mock_validator:
        mock_instance = Mock()
        mock_validator.return_value = mock_instance
        
        # Configure default behavior
        mock_instance.validate_tiss_xml.return_value = (True, [])
        mock_instance.get_schema_info.return_value = {
            "status": "loaded",
            "file_path": "/fake/path/schema.xsd",
            "file_size": 1024,
            "target_namespace": "http://www.ans.gov.br/padroes/tiss/schemas",
            "namespaces": {"xs": "http://www.w3.org/2001/XMLSchema"},
            "root_elements": ["tiss"]
        }
        mock_instance.is_schema_loaded.return_value = True
        
        yield mock_instance


@pytest.fixture
def mock_xml_generator():
    """Mock XML generator for testing."""
    with patch('services.xml_generator.TISSXMLGenerator') as mock_generator:
        mock_instance = Mock()
        mock_generator.return_value = mock_instance
        
        # Configure default behavior
        mock_instance.generate_tiss_xml.return_value = "<tiss>Sample XML</tiss>"
        mock_instance.generate_tiss_xml_with_validation.return_value = (
            "<tiss>Sample XML</tiss>", True, []
        )
        mock_instance.validate_generated_xml.return_value = (True, [])
        mock_instance.get_schema_info.return_value = {
            "status": "loaded",
            "file_path": "/fake/path/schema.xsd"
        }
        
        yield mock_instance


# Environment and configuration fixtures
@pytest.fixture
def test_env_vars():
    """Set test environment variables."""
    test_vars = {
        "API_KEYS": "test-api-key,test-api-key-2",
        "RATE_LIMIT_REQUESTS": "100",
        "RATE_LIMIT_WINDOW": "3600",
        "LOG_LEVEL": "DEBUG"
    }
    
    # Store original values
    original_values = {}
    for key, value in test_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_vars
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time
        
        def __enter__(self):
            self.start()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop()
    
    return Timer()


# Assertion helpers
def assert_valid_response_structure(response_data, expected_fields):
    """Assert that response has expected structure."""
    assert isinstance(response_data, dict)
    for field in expected_fields:
        assert field in response_data, f"Missing field: {field}"


def assert_valid_pagination_response(response_data, expected_total=None):
    """Assert that response has valid pagination structure."""
    required_fields = ["items", "total", "page", "size", "pages"]
    assert_valid_response_structure(response_data, required_fields)
    
    assert isinstance(response_data["items"], list)
    assert isinstance(response_data["total"], int)
    assert isinstance(response_data["page"], int)
    assert isinstance(response_data["size"], int)
    assert isinstance(response_data["pages"], int)
    
    if expected_total is not None:
        assert response_data["total"] == expected_total


def assert_valid_error_response(response_data):
    """Assert that error response has valid structure."""
    assert isinstance(response_data, dict)
    assert "detail" in response_data
    
    # Detail can be string, list, or dict depending on error type
    assert isinstance(response_data["detail"], (str, list, dict))


# Export helper functions and assertions
__all__ = [
    "assert_valid_response_structure",
    "assert_valid_pagination_response", 
    "assert_valid_error_response"
]