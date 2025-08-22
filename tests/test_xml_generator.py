import pytest
from services.xml_generator import TISSXMLGenerator
from models.database import SessionLocal, Base, engine
from models.patients import Patient
from models.providers import Provider
from models.health_plans import HealthPlan
from models.claims import Claim
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
from decimal import Decimal

# Test database configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_xml.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_generate_tiss_xml():
    """Test generating TISS XML for a claim"""
    # Create test data
    db = TestingSessionLocal()
    
    try:
        # Create a health plan
        health_plan = HealthPlan(
            name="Test Health Plan",
            operator_code="TEST001",
            registration_number="123456789",
            description="Test health plan for XML generation",
            active=True
        )
        db.add(health_plan)
        db.flush()
        
        # Create a patient
        patient = Patient(
            name="John Doe",
            cpf="123.456.789-01",
            birth_date=date(1990, 1, 1),
            address="123 Main St, City, State 12345",
            phone="+55 11 99999-9999",
            email="john.doe@example.com"
        )
        db.add(patient)
        db.flush()
        
        # Create a provider
        provider = Provider(
            name="City Hospital",
            cnpj="12.345.678/0001-90",
            type="hospital",
            address="789 Health Blvd, City, State 67890",
            contact="Dr. Smith",
            phone="+55 11 77777-7777",
            email="contact@cityhospital.com",
            website="https://cityhospital.com",
            active=True
        )
        db.add(provider)
        db.flush()
        
        # Create a claim
        claim = Claim(
            patient_id=patient.id,
            provider_id=provider.id,
            plan_id=health_plan.id,
            procedure_code="PROC001",
            diagnosis_code="DIAG001",
            date=date(2024, 1, 15),
            value=Decimal("150.00"),
            description="Regular checkup",
            status="pending"
        )
        db.add(claim)
        db.commit()
        
        # Test XML generation
        xml_generator = TISSXMLGenerator()
        
        # Override the database session for testing
        original_session = xml_generator.__class__.__dict__.get('SessionLocal', None)
        xml_generator.__class__.SessionLocal = TestingSessionLocal
        
        try:
            xml_content = xml_generator.generate_tiss_xml(claim.id)
            
            # Verify XML structure
            assert xml_content is not None
            assert len(xml_content) > 0
            
            # Verify XML contains expected elements
            assert '<?xml version="1.0" encoding="UTF-8"?>' in xml_content
            assert '<ans:mensagemTISS' in xml_content
            assert 'version="3.05.00"' in xml_content
            assert 'xmlns:ans="http://www.ans.gov.br/padroes/tiss/schemas"' in xml_content
            
            # Verify header section
            assert '<ans:cabecalho>' in xml_content
            assert '<ans:identificacaoOperadora>' in xml_content
            assert '<ans:dadosPrestador>' in xml_content
            assert '<ans:dataProcessamento>' in xml_content
            assert '<ans:numeroProtocolo>' in xml_content
            
            # Verify body section
            assert '<ans:corpo>' in xml_content
            assert '<ans:dadosGuia>' in xml_content
            assert '<ans:identificacaoGuia>' in xml_content
            assert '<ans:dadosBeneficiario>' in xml_content
            assert '<ans:dadosPrestador>' in xml_content
            assert '<ans:dadosProfissionalExecutante>' in xml_content
            assert '<ans:dadosProcedimento>' in xml_content
            assert '<ans:diagnostico>' in xml_content
            assert '<ans:valoresInformados>' in xml_content
            
            # Verify footer section
            assert '<ans:rodape>' in xml_content
            
            # Verify specific data
            assert patient.name in xml_content
            assert patient.cpf in xml_content
            assert provider.cnpj in xml_content
            assert health_plan.operator_code in xml_content
            assert str(claim.value) in xml_content
            assert claim.procedure_code in xml_content
            assert claim.diagnosis_code in xml_content
            
        finally:
            # Restore original session
            if original_session:
                xml_generator.__class__.SessionLocal = original_session
            else:
                delattr(xml_generator.__class__, 'SessionLocal')
                
    finally:
        db.close()

def test_generate_tiss_xml_claim_not_found():
    """Test XML generation with non-existent claim ID"""
    xml_generator = TISSXMLGenerator()
    
    # Override the database session for testing
    original_session = xml_generator.__class__.__dict__.get('SessionLocal', None)
    xml_generator.__class__.SessionLocal = TestingSessionLocal
    
    try:
        with pytest.raises(ValueError, match="Claim with ID 999 not found"):
            xml_generator.generate_tiss_xml(999)
    finally:
        # Restore original session
        if original_session:
            xml_generator.__class__.SessionLocal = original_session
        else:
            delattr(xml_generator.__class__, 'SessionLocal')

def test_generate_tiss_xml_missing_related_data():
    """Test XML generation with missing related data"""
    # Create test data with missing health plan
    db = TestingSessionLocal()
    
    try:
        # Create a patient
        patient = Patient(
            name="Jane Doe",
            cpf="987.654.321-09",
            birth_date=date(1985, 5, 15),
            address="456 Oak Ave, City, State 54321",
            phone="+55 11 88888-8888",
            email="jane.doe@example.com"
        )
        db.add(patient)
        db.flush()
        
        # Create a provider
        provider = Provider(
            name="Medical Clinic",
            cnpj="98.765.432/0001-10",
            type="clinic",
            address="654 Care Lane, City, State 22222",
            contact="Dr. Johnson",
            phone="+55 11 55555-5555",
            email="contact@medicalclinic.com",
            active=True
        )
        db.add(provider)
        db.flush()
        
        # Create a claim with non-existent health plan ID
        claim = Claim(
            patient_id=patient.id,
            provider_id=provider.id,
            plan_id=999,  # Non-existent health plan
            procedure_code="PROC002",
            diagnosis_code="DIAG002",
            date=date(2024, 1, 16),
            value=Decimal("200.00"),
            description="Special consultation",
            status="pending"
        )
        db.add(claim)
        db.commit()
        
        # Test XML generation
        xml_generator = TISSXMLGenerator()
        
        # Override the database session for testing
        original_session = xml_generator.__class__.__dict__.get('SessionLocal', None)
        xml_generator.__class__.SessionLocal = TestingSessionLocal
        
        try:
            with pytest.raises(ValueError, match="Health plan with ID 999 not found"):
                xml_generator.generate_tiss_xml(claim.id)
        finally:
            # Restore original session
            if original_session:
                xml_generator.__class__.SessionLocal = original_session
            else:
                delattr(xml_generator.__class__, 'SessionLocal')
                
    finally:
        db.close()

def test_tiss_xml_structure():
    """Test that generated XML follows TISS 3.05.00 structure"""
    # Create minimal test data
    db = TestingSessionLocal()
    
    try:
        # Create a health plan
        health_plan = HealthPlan(
            name="Minimal Health Plan",
            operator_code="MIN001",
            registration_number="987654321",
            description="Minimal health plan",
            active=True
        )
        db.add(health_plan)
        db.flush()
        
        # Create a patient
        patient = Patient(
            name="Minimal Patient",
            cpf="111.222.333-44",
            birth_date=date(1995, 10, 20),
            address="Minimal Address, City, State",
            phone="+55 11 11111-1111",
            email="minimal@example.com"
        )
        db.add(patient)
        db.flush()
        
        # Create a provider
        provider = Provider(
            name="Minimal Provider",
            cnpj="11.111.111/0001-11",
            type="clinic",
            address="Minimal Provider Address",
            contact="Dr. Minimal",
            phone="+55 11 22222-2222",
            email="minimal@provider.com",
            active=True
        )
        db.add(provider)
        db.flush()
        
        # Create a claim
        claim = Claim(
            patient_id=patient.id,
            provider_id=provider.id,
            plan_id=health_plan.id,
            procedure_code="MIN001",
            diagnosis_code="MIN001",
            date=date(2024, 1, 17),
            value=Decimal("100.00"),
            description="Minimal procedure",
            status="pending"
        )
        db.add(claim)
        db.commit()
        
        # Test XML generation
        xml_generator = TISSXMLGenerator()
        
        # Override the database session for testing
        original_session = xml_generator.__class__.__dict__.get('SessionLocal', None)
        xml_generator.__class__.SessionLocal = TestingSessionLocal
        
        try:
            xml_content = xml_generator.generate_tiss_xml(claim.id)
            
            # Verify XML is well-formed
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            # Verify root element
            assert root.tag == "ans:mensagemTISS"
            assert root.get("version") == "3.05.00"
            assert root.get("xmlns:ans") == "http://www.ans.gov.br/padroes/tiss/schemas"
            
            # Verify required sections exist
            header = root.find("ans:cabecalho")
            assert header is not None
            
            body = root.find("ans:corpo")
            assert body is not None
            
            footer = root.find("ans:rodape")
            assert footer is not None
            
            # Verify header structure
            operadora = header.find("ans:identificacaoOperadora")
            assert operadora is not None
            assert operadora.find("ans:codigoOperadora").text == health_plan.operator_code
            assert operadora.find("ans:registroANS").text == health_plan.registration_number
            
            # Verify body structure
            dados_guia = body.find("ans:dadosGuia")
            assert dados_guia is not None
            
            # Verify footer structure
            prestador_footer = footer.find("ans:dadosPrestador")
            assert prestador_footer is not None
            assert prestador_footer.find("ans:cnpjPrestador").text == provider.cnpj
            
        finally:
            # Restore original session
            if original_session:
                xml_generator.__class__.SessionLocal = original_session
            else:
                delattr(xml_generator.__class__, 'SessionLocal')
                
    finally:
        db.close() 