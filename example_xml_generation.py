#!/usr/bin/env python3
"""
Example script demonstrating TISS XML generation

This script shows how to use the new generate_tiss_xml function
to generate TISS 3.05.00 compliant XML for healthcare claims.
"""

import os
import sys
from datetime import date
from decimal import Decimal

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.xml_generator import TISSXMLGenerator
from models.database import SessionLocal, init_db
from models.patients import Patient
from models.providers import Provider
from models.health_plans import HealthPlan
from models.claims import Claim

def create_sample_data():
    """Create sample data for XML generation demonstration"""
    db = SessionLocal()
    
    try:
        # Create a health plan
        health_plan = HealthPlan(
            name="Premium Health Insurance",
            operator_code="PREMIUM001",
            registration_number="123456789",
            description="Premium health insurance plan",
            active=True
        )
        db.add(health_plan)
        db.flush()
        print(f"✓ Created health plan: {health_plan.name} (ID: {health_plan.id})")
        
        # Create a patient
        patient = Patient(
            name="Maria Silva",
            cpf="123.456.789-01",
            birth_date=date(1985, 6, 15),
            address="Rua das Flores, 123, São Paulo, SP 01234-567",
            phone="+55 11 98765-4321",
            email="maria.silva@email.com"
        )
        db.add(patient)
        db.flush()
        print(f"✓ Created patient: {patient.name} (ID: {patient.id})")
        
        # Create a provider
        provider = Provider(
            name="Hospital São Lucas",
            cnpj="12.345.678/0001-90",
            type="hospital",
            address="Av. Paulista, 1000, São Paulo, SP 01310-100",
            contact="Dr. Carlos Santos",
            phone="+55 11 3456-7890",
            email="contato@hospitalsaolucas.com.br",
            website="https://hospitalsaolucas.com.br",
            active=True
        )
        db.add(provider)
        db.flush()
        print(f"✓ Created provider: {provider.name} (ID: {provider.id})")
        
        # Create a claim
        claim = Claim(
            patient_id=patient.id,
            provider_id=provider.id,
            plan_id=health_plan.id,
            procedure_code="10101012",
            diagnosis_code="Z00.0",
            date=date(2024, 1, 20),
            value=Decimal("250.00"),
            description="Consulta médica de rotina",
            status="approved"
        )
        db.add(claim)
        db.commit()
        print(f"✓ Created claim: ID {claim.id}, Value: R$ {claim.value}")
        
        return claim.id
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error creating sample data: {e}")
        return None
    finally:
        db.close()

def generate_xml_example(claim_id: int):
    """Generate TISS XML for the specified claim"""
    try:
        print(f"\n🔄 Generating TISS XML for claim ID: {claim_id}")
        
        # Create XML generator
        xml_generator = TISSXMLGenerator()
        
        # Generate XML
        xml_content = xml_generator.generate_tiss_xml(claim_id)
        
        print("✓ TISS XML generated successfully!")
        print(f"📄 XML Length: {len(xml_content)} characters")
        
        # Save XML to file
        filename = f"tiss_claim_{claim_id}_{date.today().strftime('%Y%m%d')}.xml"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"💾 XML saved to: {filename}")
        
        # Display XML preview
        print("\n📋 XML Preview (first 500 characters):")
        print("-" * 50)
        print(xml_content[:500] + "..." if len(xml_content) > 500 else xml_content)
        print("-" * 50)
        
        return xml_content
        
    except Exception as e:
        print(f"✗ Error generating XML: {e}")
        return None

def main():
    """Main function to demonstrate XML generation"""
    print("🏥 TISS XML Generation Example")
    print("=" * 50)
    
    # Initialize database
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return
    
    # Create sample data
    claim_id = create_sample_data()
    if not claim_id:
        print("✗ Failed to create sample data")
        return
    
    # Generate XML
    xml_content = generate_xml_example(claim_id)
    
    if xml_content:
        print("\n🎉 XML generation completed successfully!")
        print("\n📚 What was generated:")
        print("  • TISS 3.05.00 compliant XML structure")
        print("  • Header with health insurance and provider information")
        print("  • Body with claim, patient, and procedure details")
        print("  • Footer with summary information")
        print("  • Proper XML namespaces and formatting")
    else:
        print("\n❌ XML generation failed")

if __name__ == "__main__":
    main() 