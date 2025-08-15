
-- Advanced demo schema with ML-ready data
CREATE SCHEMA IF NOT EXISTS advanced_demo;

-- Enhanced customers table with ML features
CREATE TABLE advanced_demo.customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INTEGER,
    country VARCHAR(50),
    acquisition_channel VARCHAR(50),
    customer_segment VARCHAR(20),
    lifetime_value DECIMAL(10,2) DEFAULT 0,
    order_frequency INTEGER DEFAULT 0,
    avg_order_value DECIMAL(10,2) DEFAULT 0,
    days_since_last_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for ML analysis
CREATE INDEX idx_adv_customers_created_at ON advanced_demo.customers(created_at);
CREATE INDEX idx_adv_customers_country ON advanced_demo.customers(country);
CREATE INDEX idx_adv_customers_segment ON advanced_demo.customers(customer_segment);
