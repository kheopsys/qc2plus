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

-- Orders with normal pattern (baseline)
INSERT INTO basic_demo.orders (customer_id, order_date, total_amount, status) VALUES
-- Normal days (10-15 orders per day)
(1, CURRENT_DATE - INTERVAL '30 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '30 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '30 days', 200.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '29 days', 180.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '29 days', 95.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '29 days', 120.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '29 days', 250.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '29 days', 85.00, 'completed'),
-- Continue normal pattern for 28 days...
(1, CURRENT_DATE - INTERVAL '28 days', 160.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '28 days', 90.00, 'completed'),
(3, CURRENT_DATE - INTERVAL '28 days', 210.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '28 days', 135.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '28 days', 175.00, 'completed'),

-- SPIKE DAY: +30% orders due to marketing campaign
(1, CURRENT_DATE - INTERVAL '3 days', 150.00, 'completed'),
(2, CURRENT_DATE - INTERVAL '3 days', 75.50, 'completed'),
(3, CURRENT_DATE - INTERVAL '3 days', 200.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '3 days', 180.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '3 days', 95.00, 'completed'),
(1, CURRENT_DATE - INTERVAL '3 days', 220.00, 'completed'),  -- Extra orders (+30%)
(2, CURRENT_DATE - INTERVAL '3 days', 130.00, 'completed'),  
(3, CURRENT_DATE - INTERVAL '3 days', 165.00, 'completed'),
(4, CURRENT_DATE - INTERVAL '3 days', 145.00, 'completed'),
(5, CURRENT_DATE - INTERVAL '3 days', 190.00, 'completed'),

-- Invalid order for testing
(999, CURRENT_DATE - INTERVAL '2 days', 100.00, 'completed'); -- Invalid customer_id

-- Create user sessions table to explain the spike
CREATE TABLE IF NOT EXISTS basic_demo.user_sessions (
    session_id SERIAL PRIMARY KEY,
    session_date DATE NOT NULL,
    user_count INTEGER NOT NULL,
    page_views INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Normal session data (baseline: ~1000 users/day)
INSERT INTO basic_demo.user_sessions (session_date, user_count, page_views) VALUES
(CURRENT_DATE - INTERVAL '30 days', 950, 4200),
(CURRENT_DATE - INTERVAL '29 days', 1020, 4800),
(CURRENT_DATE - INTERVAL '28 days', 980, 4300),
(CURRENT_DATE - INTERVAL '27 days', 1050, 4900),
(CURRENT_DATE - INTERVAL '26 days', 1000, 4500),
(CURRENT_DATE - INTERVAL '25 days', 970, 4100),
(CURRENT_DATE - INTERVAL '24 days', 1030, 4700),
(CURRENT_DATE - INTERVAL '23 days', 990, 4400),
(CURRENT_DATE - INTERVAL '22 days', 1010, 4600),
(CURRENT_DATE - INTERVAL '21 days', 960, 4200),
(CURRENT_DATE - INTERVAL '20 days', 1040, 4800),
(CURRENT_DATE - INTERVAL '19 days', 980, 4300),
(CURRENT_DATE - INTERVAL '18 days', 1020, 4700),
(CURRENT_DATE - INTERVAL '17 days', 1000, 4500),
(CURRENT_DATE - INTERVAL '16 days', 970, 4200),
(CURRENT_DATE - INTERVAL '15 days', 1030, 4600),
(CURRENT_DATE - INTERVAL '14 days', 990, 4400),
(CURRENT_DATE - INTERVAL '13 days', 1010, 4500),
(CURRENT_DATE - INTERVAL '12 days', 980, 4300),
(CURRENT_DATE - INTERVAL '11 days', 1020, 4700),
(CURRENT_DATE - INTERVAL '10 days', 1000, 4500),
(CURRENT_DATE - INTERVAL '9 days', 970, 4200),
(CURRENT_DATE - INTERVAL '8 days', 1030, 4600),
(CURRENT_DATE - INTERVAL '7 days', 990, 4400),
(CURRENT_DATE - INTERVAL '6 days', 1010, 4500),
(CURRENT_DATE - INTERVAL '5 days', 980, 4300),
(CURRENT_DATE - INTERVAL '4 days', 1000, 4500),

-- SPIKE DAY: +40% users due to marketing campaign (same day as orders spike)
(CURRENT_DATE - INTERVAL '3 days', 1400, 6300),  -- +40% users, +40% page views

-- Back to normal
(CURRENT_DATE - INTERVAL '2 days', 1010, 4500),
(CURRENT_DATE - INTERVAL '1 days', 990, 4400);

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