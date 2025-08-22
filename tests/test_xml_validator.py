import pytest
import tempfile
import os
from pathlib import Path
from services.xml_validator import TISSXMLValidator

class TestTISSXMLValidator:
    """Test class for TISS XML Validator"""
    
    @pytest.fixture
    def temp_xsd_dir(self):
        """Create a temporary directory for XSD files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def validator(self, temp_xsd_dir):
        """Create validator instance with temporary directory"""
        return TISSXMLValidator(xsd_directory=temp_xsd_dir)
    
    def test_validator_initialization(self, validator):
        """Test validator initialization"""
        assert validator is not None
        assert hasattr(validator, 'xsd_directory')
        assert hasattr(validator, 'tiss_xsd_file')
    
    def test_xsd_file_exists_false(self, validator):
        """Test XSD file existence check when file doesn't exist"""
        assert not validator.xsd_file_exists()
    
    def test_create_basic_tiss_xsd(self, validator):
        """Test creation of basic TISS XSD schema"""
        result = validator.create_basic_tiss_xsd()
        assert result is True
        assert validator.xsd_file_exists()
        
        # Check file content
        with open(validator.tiss_xsd_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<?xml version="1.0" encoding="UTF-8"?>' in content
            assert '<xs:schema' in content
            assert 'targetNamespace="http://www.ans.gov.br/padroes/tiss/schemas"' in content
    
    def test_schema_info_not_found(self, validator):
        """Test schema info when XSD file doesn't exist"""
        info = validator.get_schema_info()
        assert info["status"] == "not_found"
        assert "message" in info
    
    def test_schema_info_loaded(self, validator):
        """Test schema info when XSD file exists"""
        # Create basic XSD first
        validator.create_basic_tiss_xsd()
        
        info = validator.get_schema_info()
        assert info["status"] == "loaded"
        assert "file_path" in info
        assert "file_size" in info
        assert "target_namespace" in info
        assert "namespaces" in info
        assert "root_elements" in info
    
    def test_is_schema_loaded_false(self, validator):
        """Test schema loaded check when no XSD file exists"""
        assert not validator.is_schema_loaded()
    
    def test_is_schema_loaded_true(self, validator):
        """Test schema loaded check when XSD file exists and is valid"""
        # Create basic XSD first
        validator.create_basic_tiss_xsd()
        
        assert validator.is_schema_loaded()
    
    def test_validate_tiss_xml_no_schema(self, validator):
        """Test XML validation when no XSD schema exists"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ans:mensagemTISS xmlns:ans="http://www.ans.gov.br/padroes/tiss/schemas" version="3.05.00">
    <ans:cabecalho>
        <ans:identificacaoOperadora>
            <ans:codigoOperadora>TEST001</ans:codigoOperadora>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:identificacaoOperadora>
        <ans:dadosPrestador>
            <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:dadosPrestador>
        <ans:dataProcessamento>2024-01-15</ans:dataProcessamento>
        <ans:numeroProtocolo>1</ans:numeroProtocolo>
    </ans:cabecalho>
    <ans:corpo>
        <ans:dadosGuia>
            <ans:identificacaoGuia>
                <ans:numeroGuiaPrestador>1</ans:numeroGuiaPrestador>
                <ans:numeroGuiaOperadora>1</ans:numeroGuiaOperadora>
                <ans:dataAutorizacao>2024-01-15</ans:dataAutorizacao>
                <ans:senha>123456</ans:senha>
                <ans:dataValidadeSenha>2024-02-15</ans:dataValidadeSenha>
            </ans:identificacaoGuia>
            <ans:dadosBeneficiario>
                <ans:numeroCarteira>1</ans:numeroCarteira>
                <ans:nomeBeneficiario>John Doe</ans:nomeBeneficiario>
                <ans:dataNascimento>1990-01-01</ans:dataNascimento>
                <ans:sexo>I</ans:sexo>
                <ans:cpf>123.456.789-01</ans:cpf>
            </ans:dadosBeneficiario>
            <ans:dadosPrestador>
                <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
                <ans:nomePrestador>Test Hospital</ans:nomePrestador>
                <ans:enderecoPrestador>Test Address</ans:enderecoPrestador>
            </ans:dadosPrestador>
            <ans:dadosProfissionalExecutante>
                <ans:nomeProfissional>Dr. Test</ans:nomeProfissional>
                <ans:conselhoProfissional>CRM</ans:conselhoProfissional>
                <ans:numeroRegistroProfissional>12345</ans:numeroRegistroProfissional>
                <ans:ufConselho>SP</ans:ufConselho>
                <ans:cbos>225103</ans:cbos>
            </ans:dadosProfissionalExecutante>
            <ans:dadosProcedimento>
                <ans:codigoProcedimento>PROC001</ans:codigoProcedimento>
                <ans:descricaoProcedimento>Test Procedure</ans:descricaoProcedimento>
                <ans:dataProcedimento>2024-01-15</ans:dataProcedimento>
                <ans:valorProcedimento>150.00</ans:valorProcedimento>
            </ans:dadosProcedimento>
            <ans:diagnostico>
                <ans:codigoDiagnostico>DIAG001</ans:codigoDiagnostico>
                <ans:descricaoDiagnostico>Test Diagnosis</ans:descricaoDiagnostico>
            </ans:diagnostico>
            <ans:valoresInformados>
                <ans:valorTotalGeral>150.00</ans:valorTotalGeral>
                <ans:valorTotalProcedimentos>150.00</ans:valorTotalProcedimentos>
            </ans:valoresInformados>
        </ans:dadosGuia>
    </ans:corpo>
    <ans:rodape>
        <ans:dadosPrestador>
            <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:dadosPrestador>
        <ans:dataProcessamento>2024-01-15</ans:dataProcessamento>
        <ans:valorTotalGeral>150.00</ans:valorTotalGeral>
    </ans:rodape>
</ans:mensagemTISS>"""
        
        is_valid, errors = validator.validate_tiss_xml(xml_content)
        assert not is_valid
        assert len(errors) > 0
        assert "TISS XSD schema file not found" in errors[0]
    
    def test_validate_tiss_xml_with_schema(self, validator):
        """Test XML validation with valid XSD schema"""
        # Create basic XSD first
        validator.create_basic_tiss_xsd()
        
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ans:mensagemTISS xmlns:ans="http://www.ans.gov.br/padroes/tiss/schemas" version="3.05.00">
    <ans:cabecalho>
        <ans:identificacaoOperadora>
            <ans:codigoOperadora>TEST001</ans:codigoOperadora>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:identificacaoOperadora>
        <ans:dadosPrestador>
            <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:dadosPrestador>
        <ans:dataProcessamento>2024-01-15</ans:dataProcessamento>
        <ans:numeroProtocolo>1</ans:numeroProtocolo>
    </ans:cabecalho>
    <ans:corpo>
        <ans:dadosGuia>
            <ans:identificacaoGuia>
                <ans:numeroGuiaPrestador>1</ans:numeroGuiaPrestador>
                <ans:numeroGuiaOperadora>1</ans:numeroGuiaOperadora>
                <ans:dataAutorizacao>2024-01-15</ans:dataAutorizacao>
                <ans:senha>123456</ans:senha>
                <ans:dataValidadeSenha>2024-02-15</ans:dataValidadeSenha>
            </ans:identificacaoGuia>
            <ans:dadosBeneficiario>
                <ans:numeroCarteira>1</ans:numeroCarteira>
                <ans:nomeBeneficiario>John Doe</ans:nomeBeneficiario>
                <ans:dataNascimento>1990-01-01</ans:dataNascimento>
                <ans:sexo>I</ans:sexo>
                <ans:cpf>123.456.789-01</ans:cpf>
            </ans:dadosBeneficiario>
            <ans:dadosPrestador>
                <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
                <ans:nomePrestador>Test Hospital</ans:nomePrestador>
                <ans:enderecoPrestador>Test Address</ans:enderecoPrestador>
            </ans:dadosPrestador>
            <ans:dadosProfissionalExecutante>
                <ans:nomeProfissional>Dr. Test</ans:nomeProfissional>
                <ans:conselhoProfissional>CRM</ans:conselhoProfissional>
                <ans:numeroRegistroProfissional>12345</ans:numeroRegistroProfissional>
                <ans:ufConselho>SP</ans:ufConselho>
                <ans:cbos>225103</ans:cbos>
            </ans:dadosProfissionalExecutante>
            <ans:dadosProcedimento>
                <ans:codigoProcedimento>PROC001</ans:codigoProcedimento>
                <ans:descricaoProcedimento>Test Procedure</ans:descricaoProcedimento>
                <ans:dataProcedimento>2024-01-15</ans:dataProcedimento>
                <ans:valorProcedimento>150.00</ans:valorProcedimento>
            </ans:dadosProcedimento>
            <ans:diagnostico>
                <ans:codigoDiagnostico>DIAG001</ans:codigoDiagnostico>
                <ans:descricaoDiagnostico>Test Diagnosis</ans:descricaoDiagnostico>
            </ans:diagnostico>
            <ans:valoresInformados>
                <ans:valorTotalGeral>150.00</ans:valorTotalGeral>
                <ans:valorTotalProcedimentos>150.00</ans:valorTotalProcedimentos>
            </ans:valoresInformados>
        </ans:dadosGuia>
    </ans:corpo>
    <ans:rodape>
        <ans:dadosPrestador>
            <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:dadosPrestador>
        <ans:dataProcessamento>2024-01-15</ans:dataProcessamento>
        <ans:valorTotalGeral>150.00</ans:valorTotalGeral>
    </ans:rodape>
</ans:mensagemTISS>"""
        
        is_valid, errors = validator.validate_tiss_xml(xml_content)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_tiss_xml_invalid_structure(self, validator):
        """Test XML validation with invalid structure"""
        # Create basic XSD first
        validator.create_basic_tiss_xsd()
        
        # Invalid XML - missing required elements
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ans:mensagemTISS xmlns:ans="http://www.ans.gov.br/padroes/tiss/schemas" version="3.05.00">
    <ans:cabecalho>
        <ans:identificacaoOperadora>
            <ans:codigoOperadora>TEST001</ans:codigoOperadora>
        </ans:identificacaoOperadora>
    </ans:cabecalho>
</ans:mensagemTISS>"""
        
        is_valid, errors = validator.validate_tiss_xml(invalid_xml)
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_tiss_xml_file_not_found(self, validator):
        """Test XML file validation when file doesn't exist"""
        is_valid, errors = validator.validate_tiss_xml_file("nonexistent.xml")
        assert not is_valid
        assert len(errors) > 0
        assert "XML file not found" in errors[0]
    
    def test_validate_tiss_xml_file_valid(self, validator, temp_xsd_dir):
        """Test XML file validation with valid file"""
        # Create basic XSD first
        validator.create_basic_tiss_xsd()
        
        # Create temporary XML file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<ans:mensagemTISS xmlns:ans="http://www.ans.gov.br/padroes/tiss/schemas" version="3.05.00">
    <ans:cabecalho>
        <ans:identificacaoOperadora>
            <ans:codigoOperadora>TEST001</ans:codigoOperadora>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:identificacaoOperadora>
        <ans:dadosPrestador>
            <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:dadosPrestador>
        <ans:dataProcessamento>2024-01-15</ans:dataProcessamento>
        <ans:numeroProtocolo>1</ans:numeroProtocolo>
    </ans:cabecalho>
    <ans:corpo>
        <ans:dadosGuia>
            <ans:identificacaoGuia>
                <ans:numeroGuiaPrestador>1</ans:numeroGuiaPrestador>
                <ans:numeroGuiaOperadora>1</ans:numeroGuiaOperadora>
                <ans:dataAutorizacao>2024-01-15</ans:dataAutorizacao>
                <ans:senha>123456</ans:senha>
                <ans:dataValidadeSenha>2024-02-15</ans:dataValidadeSenha>
            </ans:identificacaoGuia>
            <ans:dadosBeneficiario>
                <ans:numeroCarteira>1</ans:numeroCarteira>
                <ans:nomeBeneficiario>John Doe</ans:nomeBeneficiario>
                <ans:dataNascimento>1990-01-01</ans:dataNascimento>
                <ans:sexo>I</ans:sexo>
                <ans:cpf>123.456.789-01</ans:cpf>
            </ans:dadosBeneficiario>
            <ans:dadosPrestador>
                <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
                <ans:nomePrestador>Test Hospital</ans:nomePrestador>
                <ans:enderecoPrestador>Test Address</ans:enderecoPrestador>
            </ans:dadosPrestador>
            <ans:dadosProfissionalExecutante>
                <ans:nomeProfissional>Dr. Test</ans:nomeProfissional>
                <ans:conselhoProfissional>CRM</ans:conselhoProfissional>
                <ans:numeroRegistroProfissional>12345</ans:numeroRegistroProfissional>
                <ans:ufConselho>SP</ans:ufConselho>
                <ans:cbos>225103</ans:cbos>
            </ans:dadosProfissionalExecutante>
            <ans:dadosProcedimento>
                <ans:codigoProcedimento>PROC001</ans:codigoProcedimento>
                <ans:descricaoProcedimento>Test Procedure</ans:descricaoProcedimento>
                <ans:dataProcedimento>2024-01-15</ans:dataProcedimento>
                <ans:valorProcedimento>150.00</ans:valorProcedimento>
            </ans:dadosProcedimento>
            <ans:diagnostico>
                <ans:codigoDiagnostico>DIAG001</ans:codigoDiagnostico>
                <ans:descricaoDiagnostico>Test Diagnosis</ans:descricaoDiagnostico>
            </ans:diagnostico>
            <ans:valoresInformados>
                <ans:valorTotalGeral>150.00</ans:valorTotalGeral>
                <ans:valorTotalProcedimentos>150.00</ans:valorTotalProcedimentos>
            </ans:valoresInformados>
        </ans:dadosGuia>
    </ans:corpo>
    <ans:rodape>
        <ans:dadosPrestador>
            <ans:cnpjPrestador>12.345.678/0001-90</ans:cnpjPrestador>
            <ans:registroANS>123456789</ans:registroANS>
        </ans:dadosPrestador>
        <ans:dataProcessamento>2024-01-15</ans:dataProcessamento>
        <ans:valorTotalGeral>150.00</ans:valorTotalGeral>
    </ans:rodape>
</ans:mensagemTISS>"""
        
        xml_file_path = os.path.join(temp_xsd_dir, "test.xml")
        with open(xml_file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        is_valid, errors = validator.validate_tiss_xml_file(xml_file_path)
        assert is_valid
        assert len(errors) == 0 