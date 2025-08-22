from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import os
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.claims import Claim
from models.patients import Patient
from models.providers import Provider
from models.health_plans import HealthPlan
from services.xml_validator import TISSXMLValidator

class TISSXMLGenerator:
    """Service for generating TISS XML files"""
    
    def __init__(self):
        self.tiss_version = "3.05.00"
        self.xmlns = "http://www.ans.gov.br/padroes/tiss/schemas"
        self.validator = TISSXMLValidator()
    
    def generate_tiss_xml(self, claim_id: int) -> str:
        """
        Generate TISS XML for a specific claim by ID
        
        Args:
            claim_id: The ID of the claim to generate XML for
            
        Returns:
            XML string according to TISS 3.05.00 standard
            
        Raises:
            ValueError: If claim or related data not found
        """
        # Get database session
        db = SessionLocal()
        try:
            # Fetch claim with related data
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if not claim:
                raise ValueError(f"Claim with ID {claim_id} not found")
            
            # Fetch related data
            patient = db.query(Patient).filter(Patient.id == claim.patient_id).first()
            if not patient:
                raise ValueError(f"Patient with ID {claim.patient_id} not found")
            
            provider = db.query(Provider).filter(Provider.id == claim.provider_id).first()
            if not provider:
                raise ValueError(f"Provider with ID {claim.provider_id} not found")
            
            health_plan = db.query(HealthPlan).filter(HealthPlan.id == claim.plan_id).first()
            if not health_plan:
                raise ValueError(f"Health plan with ID {claim.plan_id} not found")
            
            # Create root element
            root = ET.Element("ans:mensagemTISS", {
                "xmlns:ans": self.xmlns,
                "version": self.tiss_version
            })
            
            # Add header
            header = self._create_tiss_header(claim, patient, provider, health_plan)
            root.append(header)
            
            # Add body with claim data
            body = self._create_tiss_body(claim, patient, provider, health_plan)
            root.append(body)
            
            # Add footer
            footer = self._create_tiss_footer(claim, provider)
            root.append(footer)
            
            # Generate XML string with proper formatting
            xml_string = ET.tostring(root, encoding='unicode', method='xml')
            
            return xml_string
            
        except Exception as e:
            raise ValueError(f"Error generating XML: {str(e)}")
        finally:
            db.close()
    
    def generate_tiss_xml_with_validation(self, claim_id: int) -> Tuple[str, bool, List[str]]:
        """
        Generate TISS XML for a specific claim by ID with validation
        
        Args:
            claim_id: The ID of the claim to generate XML for
            
        Returns:
            Tuple[str, bool, List[str]]: (xml_content, is_valid, validation_errors)
        """
        try:
            # Generate XML
            xml_content = self.generate_tiss_xml(claim_id)
            
            # Validate XML against XSD schema
            is_valid, validation_errors = self.validator.validate_tiss_xml(xml_content)
            
            return xml_content, is_valid, validation_errors
            
        except Exception as e:
            return "", False, [f"Error generating XML: {str(e)}"]
    
    def validate_generated_xml(self, xml_content: str) -> Tuple[bool, List[str]]:
        """
        Validate generated XML against TISS XSD schema
        
        Args:
            xml_content: XML content to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, validation_errors)
        """
        return self.validator.validate_tiss_xml(xml_content)
    
    def get_schema_info(self) -> dict:
        """
        Get information about the loaded XSD schema
        
        Returns:
            dict: Schema information
        """
        return self.validator.get_schema_info()
    
    def _create_tiss_header(self, claim: Claim, patient: Patient, provider: Provider, health_plan: HealthPlan) -> ET.Element:
        """Create TISS 3.05.00 compliant header section"""
        header = ET.Element("ans:cabecalho")
        
        # Health insurance operator identification
        operadora = ET.SubElement(header, "ans:identificacaoOperadora")
        ET.SubElement(operadora, "ans:codigoOperadora").text = health_plan.operator_code
        ET.SubElement(operadora, "ans:registroANS").text = health_plan.registration_number
        
        # Provider data
        prestador = ET.SubElement(header, "ans:dadosPrestador")
        ET.SubElement(prestador, "ans:cnpjPrestador").text = provider.cnpj
        ET.SubElement(prestador, "ans:registroANS").text = health_plan.registration_number  # Using health plan ANS registration
        
        # Processing date
        ET.SubElement(header, "ans:dataProcessamento").text = datetime.now().strftime("%Y-%m-%d")
        
        # Protocol number (using claim ID)
        ET.SubElement(header, "ans:numeroProtocolo").text = str(claim.id)
        
        return header
    
    def _create_tiss_body(self, claim: Claim, patient: Patient, provider: Provider, health_plan: HealthPlan) -> ET.Element:
        """Create TISS 3.05.00 compliant body section"""
        body = ET.Element("ans:corpo")
        
        # Claim data
        dados_guia = ET.SubElement(body, "ans:dadosGuia")
        
        # Claim identification
        identificacao = ET.SubElement(dados_guia, "ans:identificacaoGuia")
        ET.SubElement(identificacao, "ans:numeroGuiaPrestador").text = str(claim.id)
        ET.SubElement(identificacao, "ans:numeroGuiaOperadora").text = str(claim.id)
        ET.SubElement(identificacao, "ans:dataAutorizacao").text = claim.claim_date.strftime("%Y-%m-%d")
        ET.SubElement(identificacao, "ans:senha").text = "123456"  # Default password, should be configurable
        ET.SubElement(identificacao, "ans:dataValidadeSenha").text = (claim.claim_date + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Patient data
        beneficiario = ET.SubElement(dados_guia, "ans:dadosBeneficiario")
        ET.SubElement(beneficiario, "ans:numeroCarteira").text = str(patient.id)  # Using patient ID as card number
        ET.SubElement(beneficiario, "ans:nomeBeneficiario").text = patient.name
        ET.SubElement(beneficiario, "ans:dataNascimento").text = patient.birth_date.strftime("%Y-%m-%d")
        ET.SubElement(beneficiario, "ans:sexo").text = "I"  # Indefinido - should come from patient model
        ET.SubElement(beneficiario, "ans:cpf").text = patient.cpf
        
        # Provider data
        prestador = ET.SubElement(dados_guia, "ans:dadosPrestador")
        ET.SubElement(prestador, "ans:cnpjPrestador").text = provider.cnpj
        ET.SubElement(prestador, "ans:nomePrestador").text = provider.name
        ET.SubElement(prestador, "ans:enderecoPrestador").text = provider.address
        
        # Professional data (using provider contact as professional)
        profissional = ET.SubElement(dados_guia, "ans:dadosProfissionalExecutante")
        ET.SubElement(profissional, "ans:nomeProfissional").text = provider.contact
        ET.SubElement(profissional, "ans:conselhoProfissional").text = "CRM"  # Default, should be configurable
        ET.SubElement(profissional, "ans:numeroRegistroProfissional").text = "12345"  # Default, should be configurable
        ET.SubElement(profissional, "ans:ufConselho").text = "SP"  # Default, should be configurable
        ET.SubElement(profissional, "ans:cbos").text = "225103"  # Default CBOS code for medical doctor
        
        # Procedure data
        procedimento = ET.SubElement(dados_guia, "ans:dadosProcedimento")
        ET.SubElement(procedimento, "ans:codigoProcedimento").text = claim.procedure_code
        ET.SubElement(procedimento, "ans:descricaoProcedimento").text = claim.description or "Procedimento médico"
        ET.SubElement(procedimento, "ans:dataProcedimento").text = claim.claim_date.strftime("%Y-%m-%d")
        ET.SubElement(procedimento, "ans:valorProcedimento").text = str(claim.value)
        
        # Diagnosis data
        diagnostico = ET.SubElement(dados_guia, "ans:diagnostico")
        ET.SubElement(diagnostico, "ans:codigoDiagnostico").text = claim.diagnosis_code
        ET.SubElement(diagnostico, "ans:descricaoDiagnostico").text = "Diagnóstico médico"  # Should come from diagnosis table
        
        # Values
        valores = ET.SubElement(dados_guia, "ans:valoresInformados")
        ET.SubElement(valores, "ans:valorTotalGeral").text = str(claim.value)
        ET.SubElement(valores, "ans:valorTotalProcedimentos").text = str(claim.value)
        
        return body
    
    def _create_tiss_footer(self, claim: Claim, provider: Provider) -> ET.Element:
        """Create TISS 3.05.00 compliant footer section"""
        footer = ET.Element("ans:rodape")
        
        # Provider data
        prestador = ET.SubElement(footer, "ans:dadosPrestador")
        ET.SubElement(prestador, "ans:cnpjPrestador").text = provider.cnpj
        ET.SubElement(prestador, "ans:registroANS").text = "123456"  # Default ANS registration
        
        # Processing date
        ET.SubElement(footer, "ans:dataProcessamento").text = datetime.now().strftime("%Y-%m-%d")
        
        # Total values
        ET.SubElement(footer, "ans:valorTotalGeral").text = str(claim.value)
        
        return footer
    
    def generate_claim_xml(self, claim_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Generate TISS XML for a healthcare claim (legacy method)"""
        # Create root element
        root = ET.Element("ans:mensagemTISS", {
            "xmlns:ans": self.xmlns,
            "version": self.tiss_version
        })
        
        # Add header
        header = self._create_header(claim_data)
        root.append(header)
        
        # Add claim data
        claim_section = self._create_claim_section(claim_data)
        root.append(claim_section)
        
        # Add footer
        footer = self._create_footer(claim_data)
        root.append(footer)
        
        # Generate XML string
        xml_string = ET.tostring(root, encoding='unicode')
        
        # Save to file if path provided
        if output_path:
            self._save_xml(xml_string, output_path)
        
        return xml_string
    
    def _create_header(self, claim_data: Dict[str, Any]) -> ET.Element:
        """Create XML header section (legacy method)"""
        header = ET.Element("ans:cabecalho")
        
        # Health insurance info
        operadora = ET.SubElement(header, "ans:identificacaoOperadora")
        ET.SubElement(operadora, "ans:codigoOperadora").text = str(claim_data.get("ans_code", ""))
        ET.SubElement(operadora, "ans:registroANS").text = str(claim_data.get("ans_code", ""))
        
        # Provider info
        prestador = ET.SubElement(header, "ans:dadosPrestador")
        ET.SubElement(prestador, "ans:cnpjPrestador").text = claim_data.get("provider_cnpj", "")
        ET.SubElement(prestador, "ans:registroANS").text = str(claim_data.get("provider_ans_code", ""))
        
        # Processing date
        ET.SubElement(header, "ans:dataProcessamento").text = datetime.now().strftime("%Y-%m-%d")
        
        return header
    
    def _create_claim_section(self, claim_data: Dict[str, Any]) -> ET.Element:
        """Create XML claim section (legacy method)"""
        dados_guia = ET.Element("ans:dadosGuia")
        
        # Claim identification
        identificacao = ET.SubElement(dados_guia, "ans:identificacaoGuia")
        ET.SubElement(identificacao, "ans:numeroGuiaPrestador").text = claim_data.get("claim_number", "")
        
        # Patient data
        beneficiario = ET.SubElement(dados_guia, "ans:dadosBeneficiario")
        ET.SubElement(beneficiario, "ans:nomeBeneficiario").text = claim_data.get("patient_name", "")
        ET.SubElement(beneficiario, "ans:dataNascimento").text = claim_data.get("birth_date", "")
        
        # Values
        valores = ET.SubElement(dados_guia, "ans:valoresInformados")
        ET.SubElement(valores, "ans:valorTotalGeral").text = str(claim_data.get("total_amount", "0.00"))
        
        return dados_guia
    
    def _create_footer(self, claim_data: Dict[str, Any]) -> ET.Element:
        """Create XML footer section (legacy method)"""
        footer = ET.Element("ans:rodape")
        
        # Provider data
        prestador = ET.SubElement(footer, "ans:dadosPrestador")
        ET.SubElement(prestador, "ans:cnpjPrestador").text = claim_data.get("provider_cnpj", "")
        
        # Processing date
        ET.SubElement(footer, "ans:dataProcessamento").text = datetime.now().strftime("%Y-%m-%d")
        
        return footer
    
    def _save_xml(self, xml_content: str, file_path: str) -> None:
        """Save XML content to file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    
    def generate_batch_xml(self, claims: List[Dict[str, Any]], output_dir: str) -> List[str]:
        """Generate XML files for multiple claims"""
        generated_files = []
        
        for claim in claims:
            filename = f"tiss_claim_{claim.get('claim_number', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            file_path = os.path.join(output_dir, filename)
            
            xml_content = self.generate_claim_xml(claim, file_path)
            generated_files.append(file_path)
        
        return generated_files 