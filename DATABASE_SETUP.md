# Database Setup Guide for TISS Healthcare API

This guide explains how to set up and use the SQLAlchemy models and database migrations for the TISS Healthcare API.

## Overview

The system includes four main entities with proper relationships:

1. **Patients** - Healthcare beneficiaries
2. **Providers** - Healthcare service providers (hospitals, clinics, etc.)
3. **HealthPlans** - Insurance plans and coverage
4. **Claims** - Medical service claims linking patients, providers, and plans

## Models Structure

### Patients Model (`models/patients.py`)
- **Fields**: id, name, CPF, birth_date, address, phone, email, created_at, updated_at
- **Features**: 
  - CPF validation (Brazilian tax ID)
  - Email format validation
  - Phone format validation
  - Age calculation property
  - Comprehensive indexing for performance

### Providers Model (`models/providers.py`)
- **Fields**: id, name, CNPJ, type, address, contact, phone, email, website, active, created_at, updated_at
- **Features**:
  - CNPJ validation (Brazilian company registration)
  - Provider type enumeration (hospital, clinic, laboratory, etc.)
  - Active/inactive status tracking
  - Website URL validation

### HealthPlans Model (`models/health_plans.py`)
- **Fields**: id, name, operator_code, registration_number, description, active, created_at, updated_at
- **Features**:
  - Unique registration numbers
  - Active/inactive status
  - Operator code tracking

### Claims Model (`models/claims.py`)
- **Fields**: id, patient_id, provider_id, plan_id, procedure_code, diagnosis_code, date, value, description, status, created_at, updated_at
- **Features**:
  - Foreign key relationships to all other entities
  - Status tracking (pending, approved, denied, paid)
  - Value validation (positive amounts only)
  - Date validation (no future dates)

## Database Relationships

```
Patients (1) ←→ (N) Claims (N) ←→ (1) Providers
    ↑                                    ↑
    └────────── (N) Claims (N) ─────────┘
    ↑                                    ↑
HealthPlans (1) ←→ (N) Claims (N) ←→ (1) Providers
```

- **One-to-Many**: Patients → Claims, Providers → Claims, HealthPlans → Claims
- **Cascade Delete**: Deleting a patient/provider/plan will delete associated claims

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database Connection
Create a `.env` file with your database credentials:
```env
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/tiss_healthcare
```

### 3. Create Database Schema
You have several options:

#### Option A: Use the Corrected SQL Script (Recommended)
```bash
mysql -u username -p < fix_schema.sql
```

#### Option B: Use the Auto-generated Schema
```bash
mysql -u username -p < generated_schema.sql
```

#### Option C: Use Alembic Migrations (Advanced)
```bash
# Initialize Alembic (already done)
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 4. Verify Setup
```bash
mysql -u username -p tiss_healthcare -e "SHOW TABLES;"
```

## Usage Examples

### Basic Model Usage
```python
from models import Patient, Provider, HealthPlan, Claim
from models.database import get_db

# Get database session
db = next(get_db())

# Create a new patient
new_patient = Patient(
    name="João Silva",
    cpf="123.456.789-01",
    birth_date="1990-05-15",
    address="Rua das Flores, 123, Centro, São Paulo - SP",
    phone="(11) 99999-9999",
    email="joao.silva@email.com"
)

db.add(new_patient)
db.commit()

# Query patients
patients = db.query(Patient).filter(Patient.active == True).all()

# Create a claim
new_claim = Claim(
    patient_id=1,
    provider_id=1,
    plan_id=1,
    procedure_code="PROC-001",
    diagnosis_code="DIAG-001",
    date="2024-01-15",
    value=150.00,
    description="Consulta médica de rotina"
)

db.add(new_claim)
db.commit()
```

### Advanced Queries
```python
# Get claims with related data
claims = db.query(Claim).join(Patient).join(Provider).join(HealthPlan).all()

# Get claims by status
pending_claims = db.query(Claim).filter(Claim.status == "pending").all()

# Get patients with their claims
patients_with_claims = db.query(Patient).options(
    joinedload(Patient.claims)
).all()

# Get claims by date range
from datetime import date
recent_claims = db.query(Claim).filter(
    Claim.date >= date(2024, 1, 1)
).all()
```

## Indexes and Performance

The models include comprehensive indexing for optimal performance:

### Primary Indexes
- All primary keys (id fields)
- Unique constraints (CPF, CNPJ, email, registration_number)

### Secondary Indexes
- Frequently queried fields (name, date, status)
- Composite indexes for common query patterns
- Foreign key fields for join performance

### Composite Indexes
- `idx_claims_patient_date` - For patient claim history
- `idx_claims_provider_date` - For provider claim reports
- `idx_claims_date_status` - For status-based reporting

## Data Validation

### Built-in Validations
- **CPF Format**: XXX.XXX.XXX-XX pattern
- **CNPJ Format**: XX.XXX.XXX/XXXX-XX pattern
- **Email Format**: Standard email validation
- **Phone Format**: International phone number support
- **Date Validation**: No future dates for claims
- **Value Validation**: Positive amounts only

### Custom Validation Methods
```python
# Validate CPF
patient = Patient(cpf="123.456.789-01")
if patient.validate_cpf():
    print("Valid CPF")

# Validate CNPJ
provider = Provider(cnpj="12.345.678/0001-90")
if provider.validate_cnpj():
    print("Valid CNPJ")
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify MySQL server is running
   - Check credentials in `.env` file
   - Ensure PyMySQL is installed

2. **Import Errors**
   - Check Python path includes project root
   - Verify all dependencies are installed

3. **Migration Issues**
   - Use the corrected SQL script for immediate setup
   - Check Alembic configuration if using migrations

### Performance Tips

1. **Use Indexes**: All common query fields are indexed
2. **Batch Operations**: Use bulk insert/update for large datasets
3. **Connection Pooling**: Configured in database.py for optimal performance
4. **Query Optimization**: Use joinedload for related data

## Sample Data

The schema includes sample data for testing:
- 3 health plans (Basic, Premium, Corporate)
- 2 patients (João Silva, Maria Santos)
- 2 providers (Hospital São Lucas, Clínica Médica Central)
- 2 sample claims

## Next Steps

1. **Customize Models**: Add business-specific fields and methods
2. **Add Validation**: Implement additional business rules
3. **Create APIs**: Build REST endpoints using the models
4. **Add Testing**: Create unit tests for model functionality
5. **Performance Monitoring**: Monitor query performance and optimize indexes

## Support

For issues or questions:
1. Check the generated SQL files for syntax errors
2. Verify database connection settings
3. Review model relationships and constraints
4. Check Alembic configuration if using migrations 