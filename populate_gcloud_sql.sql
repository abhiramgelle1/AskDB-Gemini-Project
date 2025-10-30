-- Populate Google Cloud SQL database with sample data
-- Run this in Google Cloud SQL Studio

-- Create Programs table
CREATE TABLE IF NOT EXISTS programs (
    program_id INT AUTO_INCREMENT PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    program_identifier VARCHAR(255) UNIQUE,
    deleted_status BOOLEAN DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Contacts table (Students)
CREATE TABLE IF NOT EXISTS contacts (
    id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    student_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(50),
    birthday DATE,
    gender VARCHAR(20),
    occupation VARCHAR(100),
    job_title VARCHAR(100),
    address TEXT,
    mailing_address TEXT,
    interests TEXT,
    hobbies TEXT,
    linkedin_profile VARCHAR(255),
    facebook_profile VARCHAR(255),
    twitter_profile VARCHAR(255),
    lead_source VARCHAR(100),
    lead_status VARCHAR(50),
    rating INT,
    conversion_probability DECIMAL(5,2),
    tags TEXT,
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Create Student Programs table
CREATE TABLE IF NOT EXISTS student_programs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    program_name VARCHAR(255),
    program_id INT,
    associated_program VARCHAR(255),
    start_date DATE,
    end_date DATE,
    student_name VARCHAR(200),
    active_status BOOLEAN DEFAULT 1,
    deleted_status BOOLEAN DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES programs(program_id)
);

-- Create Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(200),
    program_id INT,
    order_number VARCHAR(100) UNIQUE,
    order_date DATE,
    order_value DECIMAL(10,2),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES programs(program_id)
);

-- Create Payments table
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_number VARCHAR(100) UNIQUE,
    payment_type VARCHAR(50),
    amount DECIMAL(10,2),
    order_id INT,
    payment_date DATE,
    payment_status VARCHAR(50) DEFAULT 'pending',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Create Cases table
CREATE TABLE IF NOT EXISTS cases (
    case_id INT AUTO_INCREMENT PRIMARY KEY,
    case_number VARCHAR(100) UNIQUE,
    subject VARCHAR(255),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    description TEXT,
    notes TEXT,
    status VARCHAR(50),
    assignment_details TEXT,
    student_name VARCHAR(200),
    deleted_status BOOLEAN DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    task_number VARCHAR(100) UNIQUE,
    title VARCHAR(255),
    category VARCHAR(100),
    description TEXT,
    notes TEXT,
    assignment_details TEXT,
    assigned_to_student VARCHAR(200),
    assigned_to_lead VARCHAR(200),
    reminder_datetime DATETIME,
    start_time DATETIME,
    end_time DATETIME,
    related_url VARCHAR(500),
    deleted_status BOOLEAN DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data

-- Sample Programs
INSERT INTO programs (program_name, program_identifier) VALUES
('Data Science Bootcamp', 'DS-2024-001'),
('Web Development Course', 'WD-2024-001'),
('Machine Learning Advanced', 'ML-2024-001');

-- Sample Contacts
INSERT INTO contacts (id, first_name, last_name, student_name, email, phone, gender, occupation, lead_status, rating) VALUES
('C001', 'John', 'Doe', 'John Doe', 'john.doe@email.com', '+1-555-0101', 'Male', 'Software Engineer', 'Active', 5),
('C002', 'Jane', 'Smith', 'Jane Smith', 'jane.smith@email.com', '+1-555-0102', 'Female', 'Data Analyst', 'Active', 4),
('C003', 'Bob', 'Johnson', 'Bob Johnson', 'bob.j@email.com', '+1-555-0103', 'Male', 'Student', 'Prospect', 3);

-- Sample Student Programs
INSERT INTO student_programs (program_name, program_id, student_name, start_date, end_date, active_status) VALUES
('Data Science Bootcamp', 1, 'John Doe', '2024-01-15', '2024-06-15', 1),
('Web Development Course', 2, 'Jane Smith', '2024-02-01', '2024-05-01', 1),
('Machine Learning Advanced', 3, 'Bob Johnson', '2024-03-01', '2024-08-01', 1);

-- Sample Orders
INSERT INTO orders (student_name, program_id, order_number, order_date, order_value) VALUES
('John Doe', 1, 'ORD-2024-001', '2024-01-10', 2500.00),
('Jane Smith', 2, 'ORD-2024-002', '2024-01-25', 1800.00),
('Bob Johnson', 3, 'ORD-2024-003', '2024-02-20', 3200.00);

-- Sample Payments
INSERT INTO payments (payment_number, payment_type, amount, order_id, payment_date, payment_status) VALUES
('PAY-2024-001', 'Credit Card', 2500.00, 1, '2024-01-10', 'done'),
('PAY-2024-002', 'Bank Transfer', 1800.00, 2, '2024-01-25', 'done'),
('PAY-2024-003', 'Credit Card', 1600.00, 3, '2024-02-20', 'pending');

-- Sample Cases
INSERT INTO cases (case_number, subject, category, status, student_name) VALUES
('CASE-001', 'Course Material Access Issue', 'Technical', 'Open', 'John Doe'),
('CASE-002', 'Payment Confirmation', 'Billing', 'Resolved', 'Jane Smith'),
('CASE-003', 'Schedule Change Request', 'Administrative', 'In Progress', 'Bob Johnson');

-- Sample Tasks
INSERT INTO tasks (task_number, title, category, assigned_to_student, start_time, end_time) VALUES
('TASK-001', 'Complete Module 1 Assignment', 'Academic', 'John Doe', '2024-01-20 09:00:00', '2024-01-25 17:00:00'),
('TASK-002', 'Submit Final Project', 'Academic', 'Jane Smith', '2024-04-20 09:00:00', '2024-04-30 23:59:00'),
('TASK-003', 'Attend Orientation', 'Administrative', 'Bob Johnson', '2024-03-05 10:00:00', '2024-03-05 12:00:00');

-- Verify the data
SELECT 'Programs' as TableName, COUNT(*) as RecordCount FROM programs
UNION ALL
SELECT 'Contacts', COUNT(*) FROM contacts
UNION ALL
SELECT 'Student_Programs', COUNT(*) FROM student_programs
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Payments', COUNT(*) FROM payments
UNION ALL
SELECT 'Cases', COUNT(*) FROM cases
UNION ALL
SELECT 'Tasks', COUNT(*) FROM tasks;

-- Done!
SELECT 'Google Cloud SQL database setup complete! ✅' as Status;
