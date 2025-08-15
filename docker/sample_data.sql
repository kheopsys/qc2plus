
-- Sample data for BASIC schema
INSERT INTO basic_demo.customers (email, first_name, last_name, age, status, country) VALUES
('john.doe@email.com', 'John', 'Doe', 35, 'active', 'USA'),
('jane.smith@email.com', 'Jane', 'Smith', 28, 'active', 'UK'),
('bob.johnson@email.com', 'Bob', 'Johnson', 42, 'active', 'Canada'),
('alice.brown@email.com', 'Alice', 'Brown', 31, 'inactive', 'USA'),
('charlie.wilson@email.com', 'Charlie', 'Wilson', 29, 'active', 'UK');

-- Problematic data for testing
INSERT INTO basic_demo.customers (email, first_name, last_name, age, status, country) VALUES
('invalid-email', 'Test', 'User1', 25, 'active', 'USA'),  -- Invalid email
('test2@email.com', 'Test', 'User2', 150, 'active', 'USA'); -- Invalid age

INSERT INTO basic_demo.orders (customer_id, order_date, total_amount, status) VALUES
(1, '2024-01-15', 150.00, 'completed'),
(2, '2024-01-16', 75.50, 'completed'),
(3, '2024-01-17', 200.00, 'pending'),
(999, '2024-01-25', 100.00, 'completed'); -- Invalid customer_id

-- Sample data for ADVANCED schema  
INSERT INTO advanced_demo.customers (
    email, first_name, last_name, age, country, acquisition_channel, 
    customer_segment, lifetime_value, order_frequency, avg_order_value, 
    days_since_last_order
) VALUES
('premium1@email.com', 'Premium', 'User1', 35, 'USA', 'google_ads', 'premium', 2500.00, 15, 166.67, 5),
('premium2@email.com', 'Premium', 'User2', 42, 'UK', 'facebook', 'premium', 3200.00, 20, 160.00, 3),
('standard1@email.com', 'Standard', 'User1', 28, 'Canada', 'organic', 'standard', 850.00, 8, 106.25, 12),
('vip1@email.com', 'VIP', 'User1', 45, 'USA', 'referral', 'vip', 5500.00, 25, 220.00, 2),
('basic1@email.com', 'Basic', 'User1', 26, 'Spain', 'social', 'basic', 150.00, 2, 75.00, 45);
