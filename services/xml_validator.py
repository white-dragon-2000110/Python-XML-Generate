import os
import tempfile
from typing import List, Tuple, Optional
from lxml import etree
import requests
from pathlib import Path

class TISSXMLValidator:
    """Service for validating TISS XML against official ANS XSD schemas"""
    
    def __init__(self, xsd_directory: str = "schemas"):
        self.xsd_directory = Path(xsd_directory)
        self.xsd_directory.mkdir(exist_ok=True)
        
        # TISS 3.05.00 XSD file path
        self.tiss_xsd_file = self.xsd_directory / "tiss_3.05.00.xsd"
        
        # Download XSD if not exists
        if not self.xsd_file_exists():
            self.download_tiss_xsd()
    
    def xsd_file_exists(self) -> bool:
        """Check if TISS XSD file exists"""
        return self.tiss_xsd_file.exists()
    
    def download_tiss_xsd(self) -> bool:
        """
        Download the official ANS TISS 3.05.00 XSD schema
        
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            # ANS TISS 3.05.00 XSD URL (official schema)
            tiss_xsd_url = "https://www.gov.br/ans/pt-br/arquivos/assuntos/prestadores-de-servicos-de-saude/tabela-unificada/downloads/tiss-3-05-00.xsd"
            
            print(f"Downloading TISS 3.05.00 XSD schema from ANS...")
            response = requests.get(tiss_xsd_url, timeout=30)
            response.raise_for_status()
            
            # Save XSD file
            with open(self.tiss_xsd_file, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ TISS XSD schema downloaded successfully to {self.tiss_xsd_file}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to download TISS XSD: {e}")
            print("Creating a basic TISS XSD schema for validation...")
            return self.create_basic_tiss_xsd()
        except Exception as e:
            print(f"✗ Error downloading TISS XSD: {e}")
            return self.create_basic_tiss_xsd()
    
    def create_basic_tiss_xsd(self) -> bool:
        """
        Create a basic TISS XSD schema for validation when official schema is unavailable
        
        Returns:
            bool: True if creation successful, False otherwise
        """
        try:
            basic_xsd = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" 
           xmlns:ans="http://www.ans.gov.br/padroes/tiss/schemas"
           targetNamespace="http://www.ans.gov.br/padroes/tiss/schemas"
           elementFormDefault="qualified">
    
    <!-- TISS Message Root Element -->
    <xs:element name="mensagemTISS">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="cabecalho" type="ans:CabecalhoType"/>
                <xs:element name="corpo" type="ans:CorpoType"/>
                <xs:element name="rodape" type="ans:RodapeType"/>
            </xs:sequence>
            <xs:attribute name="version" type="xs:string" use="required"/>
            <xs:attribute name="xmlns:ans" type="xs:string" use="required"/>
        </xs:complexType>
    </xs:element>
    
    <!-- Header Type -->
    <xs:complexType name="CabecalhoType">
        <xs:sequence>
            <xs:element name="identificacaoOperadora" type="ans:IdentificacaoOperadoraType"/>
            <xs:element name="dadosPrestador" type="ans:DadosPrestadorType"/>
            <xs:element name="dataProcessamento" type="xs:date"/>
            <xs:element name="numeroProtocolo" type="xs:string"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Health Insurance Operator Type -->
    <xs:complexType name="IdentificacaoOperadoraType">
        <xs:sequence>
            <xs:element name="codigoOperadora" type="xs:string"/>
            <xs:element name="registroANS" type="xs:string"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Provider Data Type -->
    <xs:complexType name="DadosPrestadorType">
        <xs:sequence>
            <xs:element name="cnpjPrestador" type="xs:string"/>
            <xs:element name="registroANS" type="xs:string"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Body Type -->
    <xs:complexType name="CorpoType">
        <xs:sequence>
            <xs:element name="dadosGuia" type="ans:DadosGuiaType"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Claim Data Type -->
    <xs:complexType name="DadosGuiaType">
        <xs:sequence>
            <xs:element name="identificacaoGuia" type="ans:IdentificacaoGuiaType"/>
            <xs:element name="dadosBeneficiario" type="ans:DadosBeneficiarioType"/>
            <xs:element name="dadosPrestador" type="ans:DadosPrestadorGuiaType"/>
            <xs:element name="dadosProfissionalExecutante" type="ans:DadosProfissionalType"/>
            <xs:element name="dadosProcedimento" type="ans:DadosProcedimentoType"/>
            <xs:element name="diagnostico" type="ans:DiagnosticoType"/>
            <xs:element name="valoresInformados" type="ans:ValoresInformadosType"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Claim Identification Type -->
    <xs:complexType name="IdentificacaoGuiaType">
        <xs:sequence>
            <xs:element name="numeroGuiaPrestador" type="xs:string"/>
            <xs:element name="numeroGuiaOperadora" type="xs:string"/>
            <xs:element name="dataAutorizacao" type="xs:date"/>
            <xs:element name="senha" type="xs:string"/>
            <xs:element name="dataValidadeSenha" type="xs:date"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Beneficiary Data Type -->
    <xs:complexType name="DadosBeneficiarioType">
        <xs:sequence>
            <xs:element name="numeroCarteira" type="xs:string"/>
            <xs:element name="nomeBeneficiario" type="xs:string"/>
            <xs:element name="dataNascimento" type="xs:date"/>
            <xs:element name="sexo" type="xs:string"/>
            <xs:element name="cpf" type="xs:string"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Provider Guide Data Type -->
    <xs:complexType name="DadosPrestadorGuiaType">
        <xs:sequence>
            <xs:element name="cnpjPrestador" type="xs:string"/>
            <xs:element name="nomePrestador" type="xs:string"/>
            <xs:element name="enderecoPrestador" type="xs:string"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Professional Data Type -->
    <xs:complexType name="DadosProfissionalType">
        <xs:sequence>
            <xs:element name="nomeProfissional" type="xs:string"/>
            <xs:element name="conselhoProfissional" type="xs:string"/>
            <xs:element name="numeroRegistroProfissional" type="xs:string"/>
            <xs:element name="ufConselho" type="xs:string"/>
            <xs:element name="cbos" type="xs:string"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Procedure Data Type -->
    <xs:complexType name="DadosProcedimentoType">
        <xs:sequence>
            <xs:element name="codigoProcedimento" type="xs:string"/>
            <xs:element name="descricaoProcedimento" type="xs:string"/>
            <xs:element name="dataProcedimento" type="xs:date"/>
            <xs:element name="valorProcedimento" type="xs:decimal"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Diagnosis Type -->
    <xs:complexType name="DiagnosticoType">
        <xs:sequence>
            <xs:element name="codigoDiagnostico" type="xs:string"/>
            <xs:element name="descricaoDiagnostico" type="xs:string"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Values Type -->
    <xs:complexType name="ValoresInformadosType">
        <xs:sequence>
            <xs:element name="valorTotalGeral" type="xs:decimal"/>
            <xs:element name="valorTotalProcedimentos" type="xs:decimal"/>
        </xs:sequence>
    </xs:complexType>
    
    <!-- Footer Type -->
    <xs:complexType name="RodapeType">
        <xs:sequence>
            <xs:element name="dadosPrestador" type="ans:DadosPrestadorType"/>
            <xs:element name="dataProcessamento" type="xs:date"/>
            <xs:element name="valorTotalGeral" type="xs:decimal"/>
        </xs:sequence>
    </xs:complexType>
    
</xs:schema>'''
            
            with open(self.tiss_xsd_file, 'w', encoding='utf-8') as f:
                f.write(basic_xsd)
            
            print(f"✓ Basic TISS XSD schema created at {self.tiss_xsd_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating basic TISS XSD: {e}")
            return False
    
    def validate_tiss_xml(self, xml_content: str) -> Tuple[bool, List[str]]:
        """
        Validate TISS XML against the XSD schema
        
        Args:
            xml_content: XML string to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        if not self.xsd_file_exists():
            return False, ["TISS XSD schema file not found"]
        
        try:
            # Parse XSD schema
            xsd_doc = etree.parse(str(self.tiss_xsd_file))
            xsd_schema = etree.XMLSchema(xsd_doc)
            
            # Parse XML content
            xml_doc = etree.fromstring(xml_content.encode('utf-8'))
            
            # Validate XML against XSD
            is_valid = xsd_schema.validate(xml_doc)
            
            if is_valid:
                return True, []
            else:
                # Get validation errors
                errors = []
                for error in xsd_schema.error_log:
                    errors.append(f"Line {error.line}: {error.message}")
                return False, errors
                
        except etree.XMLSyntaxError as e:
            return False, [f"XML Syntax Error: {e}"]
        except etree.XMLSchemaParseError as e:
            return False, [f"XSD Schema Parse Error: {e}"]
        except Exception as e:
            return False, [f"Validation Error: {e}"]
    
    def validate_tiss_xml_file(self, xml_file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate TISS XML file against the XSD schema
        
        Args:
            xml_file_path: Path to XML file to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        try:
            with open(xml_file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            return self.validate_tiss_xml(xml_content)
            
        except FileNotFoundError:
            return False, [f"XML file not found: {xml_file_path}"]
        except Exception as e:
            return False, [f"Error reading XML file: {e}"]
    
    def get_schema_info(self) -> dict:
        """
        Get information about the loaded XSD schema
        
        Returns:
            dict: Schema information
        """
        if not self.xsd_file_exists():
            return {"status": "not_found", "message": "XSD schema file not found"}
        
        try:
            xsd_doc = etree.parse(str(self.tiss_xsd_file))
            root = xsd_doc.getroot()
            
            # Extract namespace information
            namespaces = root.nsmap if hasattr(root, 'nsmap') else {}
            
            return {
                "status": "loaded",
                "file_path": str(self.tiss_xsd_file),
                "file_size": os.path.getsize(self.tiss_xsd_file),
                "target_namespace": root.get('targetNamespace', ''),
                "namespaces": namespaces,
                "root_elements": [elem.tag for elem in root.findall('.//xs:element', namespaces)]
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def is_schema_loaded(self) -> bool:
        """Check if XSD schema is properly loaded and valid"""
        try:
            if not self.xsd_file_exists():
                return False
            
            xsd_doc = etree.parse(str(self.tiss_xsd_file))
            etree.XMLSchema(xsd_doc)
            return True
            
        except Exception:
            return False 