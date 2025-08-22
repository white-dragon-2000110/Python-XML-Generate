-- Generated MySQL Schema from SQLAlchemy Models
-- This file was automatically generated

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS tiss_healthcare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tiss_healthcare;

-- Drop tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS providers;
DROP TABLE IF EXISTS health_plans;


CREATE TABLE patients (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	cpf VARCHAR(14) NOT NULL, 
	birth_date DATE NOT NULL, 
	address TEXT NOT NULL, 
	phone VARCHAR(20) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	created_at VARCHAR(26), 
	updated_at VARCHAR(26), 
	PRIMARY KEY (id), 
	CONSTRAINT valid_cpf_format CHECK (cpf REGEXP '^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}$'), 
	CONSTRAINT valid_email_format CHECK (email REGEXP '^[A-Za-z0-9._%%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'), 
	CONSTRAINT valid_phone_format CHECK (phone REGEXP '^[+]?[0-9\s\(\)\-]+$'), 
	CONSTRAINT valid_birth_date CHECK (birth_date <= CURDATE()), 
	CONSTRAINT valid_name_length CHECK (LENGTH(name) >= 2), 
	CONSTRAINT valid_address_length CHECK (LENGTH(address) >= 10)
)




CREATE TABLE providers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	cnpj VARCHAR(18) NOT NULL, 
	type ENUM('HOSPITAL','CLINIC','LABORATORY','IMAGING_CENTER','SPECIALIST','GENERAL_PRACTITIONER','PHARMACY','AMBULANCE','OTHER') NOT NULL, 
	address TEXT NOT NULL, 
	contact VARCHAR(255) NOT NULL, 
	phone VARCHAR(20), 
	email VARCHAR(255), 
	website VARCHAR(255), 
	active VARCHAR(5) NOT NULL, 
	created_at VARCHAR(26), 
	updated_at VARCHAR(26), 
	PRIMARY KEY (id), 
	CONSTRAINT valid_cnpj_format CHECK (cnpj REGEXP '^[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}$'), 
	CONSTRAINT valid_email_format CHECK (email IS NULL OR email REGEXP '^[A-Za-z0-9._%%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'), 
	CONSTRAINT valid_phone_format CHECK (phone IS NULL OR phone REGEXP '^[+]?[0-9\s\(\)\-]+$'), 
	CONSTRAINT valid_website_format CHECK (website IS NULL OR website REGEXP '^https?://[^\s/$.?#].[^\s]*$'), 
	CONSTRAINT valid_active_value CHECK (active IN ('true', 'false')), 
	CONSTRAINT valid_name_length CHECK (LENGTH(name) >= 3), 
	CONSTRAINT valid_address_length CHECK (LENGTH(address) >= 10), 
	CONSTRAINT valid_contact_length CHECK (LENGTH(contact) >= 5)
)




CREATE TABLE health_plans (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	operator_code VARCHAR(20) NOT NULL, 
	registration_number VARCHAR(50) NOT NULL, 
	description TEXT, 
	active BOOL NOT NULL, 
	created_at VARCHAR(26), 
	updated_at VARCHAR(26), 
	PRIMARY KEY (id), 
	CONSTRAINT valid_name_length CHECK (LENGTH(name) >= 3), 
	CONSTRAINT valid_operator_code_length CHECK (LENGTH(operator_code) >= 2), 
	CONSTRAINT valid_registration_number_length CHECK (LENGTH(registration_number) >= 5), 
	CONSTRAINT valid_operator_code_format CHECK (operator_code REGEXP '^[A-Z0-9]+$'), 
	CONSTRAINT valid_registration_number_format CHECK (registration_number REGEXP '^[A-Z0-9\-]+$')
)




CREATE TABLE claims (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	patient_id INTEGER NOT NULL, 
	provider_id INTEGER NOT NULL, 
	plan_id INTEGER NOT NULL, 
	procedure_code VARCHAR(20) NOT NULL, 
	diagnosis_code VARCHAR(20) NOT NULL, 
	date DATE NOT NULL, 
	value NUMERIC(10, 2) NOT NULL, 
	description TEXT, 
	status VARCHAR(20) NOT NULL, 
	created_at VARCHAR(26), 
	updated_at VARCHAR(26), 
	PRIMARY KEY (id), 
	CONSTRAINT valid_claim_value CHECK (value > 0), 
	CONSTRAINT valid_claim_date CHECK (date <= CURDATE()), 
	CONSTRAINT valid_claim_status CHECK (status IN ('pending', 'approved', 'denied', 'paid')), 
	CONSTRAINT valid_procedure_code_length CHECK (LENGTH(procedure_code) >= 3), 
	CONSTRAINT valid_diagnosis_code_length CHECK (LENGTH(diagnosis_code) >= 3), 
	CONSTRAINT valid_procedure_code_format CHECK (procedure_code REGEXP '^[A-Z0-9\-]+$'), 
	CONSTRAINT valid_diagnosis_code_format CHECK (diagnosis_code REGEXP '^[A-Z0-9\-]+$'), 
	FOREIGN KEY(patient_id) REFERENCES patients (id) ON DELETE CASCADE, 
	FOREIGN KEY(provider_id) REFERENCES providers (id) ON DELETE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES health_plans (id) ON DELETE CASCADE
)



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
