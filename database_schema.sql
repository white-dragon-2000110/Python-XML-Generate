-- TISS Healthcare Database Schema
CREATE DATABASE IF NOT EXISTS tiss_healthcare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tiss_healthcare;

-- Health Insurance Companies
CREATE TABLE health_insurances (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    ans_code VARCHAR(20) UNIQUE NOT NULL,
    city VARCHAR(100),
    state VARCHAR(2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Healthcare Providers
CREATE TABLE providers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cnpj VARCHAR(18) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    ans_code VARCHAR(20) UNIQUE NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Healthcare Professionals
CREATE TABLE professionals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    provider_id INT NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    crm_crm_cro VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    specialty VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

-- Patients
CREATE TABLE patients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(1) NOT NULL,
    health_insurance_id INT,
    beneficiary_number VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (health_insurance_id) REFERENCES health_insurances(id)
);

-- Healthcare Claims
CREATE TABLE claims (
    id INT PRIMARY KEY AUTO_INCREMENT,
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    health_insurance_id INT NOT NULL,
    provider_id INT NOT NULL,
    professional_id INT NOT NULL,
    patient_id INT NOT NULL,
    claim_type VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (health_insurance_id) REFERENCES health_insurances(id),
    FOREIGN KEY (provider_id) REFERENCES providers(id),
    FOREIGN KEY (professional_id) REFERENCES professionals(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Sample Data
INSERT INTO health_insurances (cnpj, name, ans_code, city, state) VALUES
('12.345.678/0001-90', 'Unimed do Brasil', '123456', 'São Paulo', 'SP'),
('98.765.432/0001-10', 'Amil Assistência Médica', '654321', 'São Paulo', 'SP');

INSERT INTO providers (cnpj, name, ans_code, provider_type, city, state) VALUES
('22.333.444/0001-55', 'Hospital Albert Einstein', '111111', 'hospital', 'São Paulo', 'SP'),
('33.444.555/0001-66', 'Laboratório Fleury', '333333', 'laboratory', 'São Paulo', 'SP'); 