-- ==========================================================
-- NGO Information & Activity Management System
-- Database Schema Script
-- Author: [Your Name]
-- Date: [Current Date]
-- ==========================================================

-- Create Database
CREATE DATABASE ngo_management_system;
USE ngo_management_system;

-- ==========================================================
-- 1. NGO Admin Table
-- ==========================================================
CREATE TABLE ngo_admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    contact_no VARCHAR(15),
    role ENUM('SuperAdmin', 'Manager', 'Coordinator') DEFAULT 'Manager',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- 2. Volunteer Table
-- ==========================================================
CREATE TABLE volunteer (
    volunteer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    gender ENUM('Male', 'Female', 'Other'),
    date_of_birth DATE,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    address TEXT,
    skills VARCHAR(255),
    join_date DATE DEFAULT (CURDATE()),
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    uri VARCHAR(255)
);


-- ==========================================================
-- 3. Donor Table
-- ==========================================================
CREATE TABLE donor (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15),
    organization_name VARCHAR(100),
    address TEXT,
    total_donations DECIMAL(12,2) DEFAULT 0,
    uri VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- 4. Beneficiary Table
-- ==========================================================
CREATE TABLE beneficiary (
    beneficiary_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    gender ENUM('Male', 'Female', 'Other'),
    age INT,
    email VARCHAR(100),
    phone VARCHAR(15),
    address TEXT,
    need_description TEXT,
    status ENUM('Active', 'Completed', 'Pending') DEFAULT 'Active',
    uri VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================
-- 5. Event Table
-- ==========================================================
CREATE TABLE event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(150) NOT NULL,
    event_date DATE NOT NULL,
    location VARCHAR(255),
    description TEXT,
    budget DECIMAL(10,2),
    status ENUM('Planning', 'Active', 'Completed', 'On Hold') DEFAULT 'Planning',
    created_by INT,
    FOREIGN KEY (created_by) REFERENCES ngo_admin(admin_id)
        ON DELETE SET NULL
);

-- ==========================================================
-- 6. Participation Table (Many-to-Many Volunteer ↔ Event)
-- ==========================================================
CREATE TABLE participation (
    participation_id INT AUTO_INCREMENT PRIMARY KEY,
    volunteer_id INT,
    event_id INT,
    role VARCHAR(100),
    hours_worked DECIMAL(5,2),
    feedback TEXT,
    FOREIGN KEY (volunteer_id) REFERENCES volunteer(volunteer_id)
        ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES event(event_id)
        ON DELETE CASCADE
);

-- ==========================================================
-- 7. Donation Table
-- ==========================================================
CREATE TABLE donation (
    donation_id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT,
    event_id INT,
    donation_date DATE DEFAULT (CURRENT_DATE),
    amount DECIMAL(10,2),
    donation_type ENUM('Cash', 'Material', 'Service') DEFAULT 'Cash',
    notes TEXT,
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id)
        ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES event(event_id)
        ON DELETE SET NULL
);

-- ==========================================================
-- 8. Resource Table
-- ==========================================================
CREATE TABLE resource (
    resource_id INT AUTO_INCREMENT PRIMARY KEY,
    resource_name VARCHAR(100),
    category VARCHAR(50),
    quantity INT,
    unit VARCHAR(20),
    event_id INT,
    allocated_to INT,
    FOREIGN KEY (event_id) REFERENCES event(event_id)
        ON DELETE SET NULL,
    FOREIGN KEY (allocated_to) REFERENCES beneficiary(beneficiary_id)
        ON DELETE SET NULL
);

-- ==========================================================
-- 9. Backup Log Table
-- ==========================================================
CREATE TABLE backup_log (
    backup_id INT AUTO_INCREMENT PRIMARY KEY,
    backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performed_by INT,
    backup_file_name VARCHAR(255),
    status ENUM('Success', 'Failed') DEFAULT 'Success',
    FOREIGN KEY (performed_by) REFERENCES ngo_admin(admin_id)
);

-- ==========================================================
-- 10. Optional User Role Table
-- ==========================================================
CREATE TABLE user_role (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE,
    description TEXT
);

-- ==========================================================
-- Indexes
-- ==========================================================
CREATE INDEX idx_donor_name ON donor(full_name);
CREATE INDEX idx_event_date ON event(event_date);
CREATE INDEX idx_volunteer_name ON volunteer(full_name);

-- ==========================================================
-- Triggers
-- ==========================================================
DELIMITER $$

CREATE TRIGGER update_total_donation
AFTER INSERT ON donation
FOR EACH ROW
BEGIN
    UPDATE donor
    SET total_donations = total_donations + NEW.amount
    WHERE donor_id = NEW.donor_id;
END$$

DELIMITER ;

-- ==========================================================
-- Views
-- ==========================================================
CREATE VIEW donor_summary AS
SELECT d.donor_id, d.full_name, COUNT(do.donation_id) AS total_donations,
       SUM(do.amount) AS total_amount
FROM donor d
LEFT JOIN donation do ON d.donor_id = do.donor_id
GROUP BY d.donor_id;

CREATE VIEW event_report AS
SELECT e.event_name, COUNT(p.volunteer_id) AS volunteers,
       SUM(do.amount) AS donations_received
FROM event e
LEFT JOIN participation p ON e.event_id = p.event_id
LEFT JOIN donation do ON e.event_id = do.event_id
GROUP BY e.event_id;

-- ==========================================================
-- Sample Data
-- ==========================================================
INSERT INTO ngo_admin (full_name, email, password_hash, contact_no, role)
VALUES 
('Ravi Sharma', 'ravi@ngo.org', 'hashed_pw_123', '9876543210', 'SuperAdmin'),
('Priya Singh', 'priya@ngo.org', 'hashed_pw_456', '9988776655', 'Coordinator');

INSERT INTO volunteer (full_name, gender, email, phone, skills)
VALUES 
('Amit Verma', 'Male', 'amit@volunteer.com', '9898989898', 'Teaching, Fundraising'),
('Sneha Patil', 'Female', 'sneha@volunteer.com', '9797979797', 'Healthcare, Communication');

INSERT INTO donor (full_name, email, phone, organization_name)
VALUES 
('Global Help Org', 'contact@globalhelp.org', '9123456780', 'Global Help Org'),
('John Doe', 'john@donor.com', '9988776655', 'Individual');

INSERT INTO beneficiary (full_name, gender, age, address, need_description)
VALUES 
('Sita Devi', 'Female', 42, 'Pune, India', 'Medical assistance'),
('Rahul Kumar', 'Male', 25, 'Nagpur, India', 'Education support');

INSERT INTO event (event_name, event_date, location, description, budget, created_by)
VALUES 
('Health Camp 2025', '2025-01-15', 'Pune', 'Free health check-up camp', 25000, 1),
('Education Drive', '2025-03-10', 'Nagpur', 'Scholarship distribution', 40000, 2);

INSERT INTO donation (donor_id, event_id, amount, donation_type, notes)
VALUES 
(1, 1, 10000, 'Cash', 'Health supplies'),
(2, 2, 5000, 'Material', 'Books and stationery');

INSERT INTO participation (volunteer_id, event_id, role, hours_worked)
VALUES 
(1, 1, 'Coordinator', 6),
(2, 2, 'Assistant', 5);

INSERT INTO resource (resource_name, category, quantity, unit, event_id, allocated_to)
VALUES 
('Medicine Kit', 'Health', 50, 'Units', 1, 1),
('Book Set', 'Education', 30, 'Sets', 2, 2);



-- ==========================================================
-- END OF SCHEMA FILE
-- ==========================================================
