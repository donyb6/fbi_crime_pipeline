-- Database Schema Reference
-- This file is simply an overview of the database schema — tables are created by their respective Python scripts (ensure_table()), not by running this file.


-- BRONZE LAYER
CREATE TABLE IF NOT EXISTS bronze_agencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_abbr VARCHAR(2) NOT NULL,
    response_json LONGTEXT NOT NULL,
    extracted_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS bronze_summarized_offenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_abbr VARCHAR(2) NOT NULL,
    offense_code VARCHAR(10) NOT NULL,
    from_date VARCHAR(7) NOT NULL,
    to_date VARCHAR(7) NOT NULL,
    response_json LONGTEXT,
    http_status INT NOT NULL,
    extracted_at DATETIME NOT NULL
);

-- SILVER LAYER
CREATE TABLE IF NOT EXISTS silver_agencies (
    ori VARCHAR(20) PRIMARY KEY,
    agency_name VARCHAR(255) NOT NULL,
    agency_type_name VARCHAR(50),
    county VARCHAR(100),
    state_abbr VARCHAR(2) NOT NULL,
    state_name VARCHAR(50),
    latitude DECIMAL(9,6) NULL,
    longitude DECIMAL(9,6) NULL,
    is_nibrs BOOLEAN,
    nibrs_start_date DATE NULL
);

CREATE TABLE IF NOT EXISTS silver_summarized_offenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_abbr VARCHAR(2) NOT NULL,
    offense_code VARCHAR(10) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    state_actual_count INT NULL,
    state_clearance_count INT NULL,
    state_rate_per_100k DECIMAL(10,4) NULL,
    state_clearance_rate_per_100k DECIMAL(10,4) NULL,
    us_actual_rate DECIMAL(10,4) NULL,
    us_clearance_rate DECIMAL(10,4) NULL,
    population INT NULL,
    participated_population INT NULL,
    UNIQUE KEY uq_state_offense_month (state_abbr, offense_code, year, month)
);


-- GOLD LAYER
CREATE TABLE IF NOT EXISTS gold_dim_offense (
    offense_code VARCHAR(10) PRIMARY KEY,
    offense_name VARCHAR(50) NOT NULL,
    category VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS gold_dim_state (
    state_abbr VARCHAR(2) PRIMARY KEY,
    state_name VARCHAR(50) NOT NULL,
    region VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS gold_dim_agency (
    ori VARCHAR(20) PRIMARY KEY,
    agency_name VARCHAR(255) NOT NULL,
    agency_type_name VARCHAR(50),
    county VARCHAR(100),
    state_abbr VARCHAR(2) NOT NULL,
    latitude DECIMAL(9,6) NULL,
    longitude DECIMAL(9,6) NULL,
    is_nibrs BOOLEAN,
    nibrs_start_date DATE NULL
);

CREATE TABLE IF NOT EXISTS gold_offense_facts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state_abbr VARCHAR(2) NOT NULL,
    offense_code VARCHAR(10) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    actual_count INT NULL,
    clearance_count INT NULL,
    clearance_rate DECIMAL(6,4) NULL,
    rate_per_100k DECIMAL(10,4) NULL,
    population INT NULL,
    UNIQUE KEY uq_state_offense_month (state_abbr, offense_code, year, month),
    FOREIGN KEY (state_abbr) REFERENCES gold_dim_state(state_abbr),
    FOREIGN KEY (offense_code) REFERENCES gold_dim_offense(offense_code)
);