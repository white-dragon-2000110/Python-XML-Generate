-- Corrected MySQL Schema for TISS Healthcare
-- This file fixes the issues in the auto-generated schema

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS tiss_healthcare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tiss_healthcare;

-- Drop tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS providers;
DROP TABLE IF EXISTS health_plans;

-- Create health_plans table
CREATE TABLE health_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    operator_code VARCHAR(20) NOT NULL,
    registration_number VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_health_plans_name (name),
    INDEX idx_health_plans_operator_code (operator_code),
    INDEX idx_health_plans_registration_number (registration_number),
    INDEX idx_health_plans_active (active),
    INDEX idx_health_plans_created_at (created_at),
    INDEX idx_health_plans_operator_active (operator_code, active),
    INDEX idx_health_plans_name_active (name, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create patients table
CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) NOT NULL UNIQUE,
    birth_date DATE NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_patients_cpf (cpf),
    INDEX idx_patients_name (name),
    INDEX idx_patients_email (email),
    INDEX idx_patients_birth_date (birth_date),
    INDEX idx_patients_created_at (created_at),
    INDEX idx_patients_name_cpf (name, cpf),
    INDEX idx_patients_cpf_email (cpf, email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create providers table
CREATE TABLE providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(18) NOT NULL UNIQUE,
    type ENUM('hospital', 'clinic', 'laboratory', 'imaging_center', 'specialist', 'general_practitioner', 'pharmacy', 'ambulance', 'other') NOT NULL,
    address TEXT NOT NULL,
    contact VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    active VARCHAR(5) DEFAULT 'true' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_providers_cnpj (cnpj),
    INDEX idx_providers_name (name),
    INDEX idx_providers_type (type),
    INDEX idx_providers_active (active),
    INDEX idx_providers_email (email),
    INDEX idx_providers_created_at (created_at),
    INDEX idx_providers_type_active (type, active),
    INDEX idx_providers_name_type (name, type),
    INDEX idx_providers_cnpj_active (cnpj, active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create claims table
CREATE TABLE claims (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    provider_id INT NOT NULL,
    plan_id INT NOT NULL,
    procedure_code VARCHAR(20) NOT NULL,
    diagnosis_code VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES health_plans(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_claims_patient_id (patient_id),
    INDEX idx_claims_provider_id (provider_id),
    INDEX idx_claims_plan_id (plan_id),
    INDEX idx_claims_procedure_code (procedure_code),
    INDEX idx_claims_diagnosis_code (diagnosis_code),
    INDEX idx_claims_date (date),
    INDEX idx_claims_value (value),
    INDEX idx_claims_status (status),
    INDEX idx_claims_created_at (created_at),
    INDEX idx_claims_patient_date (patient_id, date),
    INDEX idx_claims_provider_date (provider_id, date),
    INDEX idx_claims_plan_date (plan_id, date),
    INDEX idx_claims_procedure_diagnosis (procedure_code, diagnosis_code),
    INDEX idx_claims_date_status (date, status),
    INDEX idx_claims_patient_status (patient_id, status),
    INDEX idx_claims_provider_status (provider_id, status),
    INDEX idx_claims_plan_status (plan_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample data for testing
INSERT INTO health_plans (name, operator_code, registration_number, description) VALUES
('Plano Básico', 'OP001', 'REG-001-2024', 'Plano de saúde básico com cobertura essencial'),
('Plano Premium', 'OP001', 'REG-002-2024', 'Plano de saúde premium com cobertura ampla'),
('Plano Empresarial', 'OP002', 'REG-003-2024', 'Plano de saúde para empresas');

INSERT INTO patients (name, cpf, birth_date, address, phone, email) VALUES
('João Silva', '123.456.789-01', '1990-05-15', 'Rua das Flores, 123, Centro, São Paulo - SP', '(11) 99999-9999', 'joao.silva@email.com'),
('Maria Santos', '987.654.321-00', '1985-08-22', 'Av. Paulista, 1000, Bela Vista, São Paulo - SP', '(11) 88888-8888', 'maria.santos@email.com');

INSERT INTO providers (name, cnpj, type, address, contact, phone, email) VALUES
('Hospital São Lucas', '12.345.678/0001-90', 'hospital', 'Rua da Saúde, 500, Vila Nova, São Paulo - SP', 'Dr. Carlos Mendes', '(11) 77777-7777', 'contato@hospitalsaolucas.com'),
('Clínica Médica Central', '98.765.432/0001-10', 'clinic', 'Av. Central, 200, Centro, São Paulo - SP', 'Dra. Ana Costa', '(11) 66666-6666', 'contato@clinicacentral.com');

INSERT INTO claims (patient_id, provider_id, plan_id, procedure_code, diagnosis_code, date, value, description, status) VALUES
(1, 1, 1, 'PROC-001', 'DIAG-001', '2024-01-15', 150.00, 'Consulta médica de rotina', 'approved'),
(2, 2, 2, 'PROC-002', 'DIAG-002', '2024-01-16', 300.00, 'Exame laboratorial completo', 'pending');

-- Show table structure
SHOW TABLES;
DESCRIBE patients;
DESCRIBE providers;
DESCRIBE health_plans;
DESCRIBE claims; 