 -- Create database
CREATE DATABASE IF NOT EXISTS simnations CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE simnations;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    birth_date DATE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_active (is_active)
);

-- Create countries table
CREATE TABLE IF NOT EXISTS countries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(3) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_code (code)
);

-- Create states table
CREATE TABLE IF NOT EXISTS states (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_id INT NOT NULL,
    manager_id INT NULL,
    racionalidade DECIMAL(3,1) NOT NULL,
    conservadorismo DECIMAL(3,1) NOT NULL,
    audacia DECIMAL(3,1) NOT NULL,
    autoridade DECIMAL(3,1) NOT NULL,
    coletivismo DECIMAL(3,1) NOT NULL,
    influencia DECIMAL(3,1) NOT NULL,
    is_occupied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE CASCADE,
    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_country (country_id),
    INDEX idx_manager (manager_id),
    INDEX idx_occupied (is_occupied),
    INDEX idx_state_traits (racionalidade, conservadorismo, audacia, autoridade, coletivismo, influencia),
    INDEX idx_state_available (is_occupied, country_id),
    UNIQUE KEY unique_manager (manager_id)
);

-- Create quiz_results table
CREATE TABLE IF NOT EXISTS quiz_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    racionalidade DECIMAL(3,1) NOT NULL,
    conservadorismo DECIMAL(3,1) NOT NULL,
    audacia DECIMAL(3,1) NOT NULL,
    autoridade DECIMAL(3,1) NOT NULL,
    coletivismo DECIMAL(3,1) NOT NULL,
    influencia DECIMAL(3,1) NOT NULL,
    answers JSON NOT NULL,
    reroll_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_reroll (reroll_count),
    UNIQUE KEY unique_user_quiz (user_id)
);

-- Create indexes for better performance
CREATE INDEX idx_quiz_traits ON quiz_results(racionalidade, conservadorismo, audacia, autoridade, coletivismo, influencia);

-- Insert sample data (optional)
INSERT INTO countries (name, code) VALUES 
('Brazil', 'BRA'),
('United States', 'USA'),
('France', 'FRA'),
('Germany', 'DEU'),
('Japan', 'JPN')
ON DUPLICATE KEY UPDATE name = VALUES(name);