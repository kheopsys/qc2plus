
-- Basic demo schema and tables
CREATE SCHEMA IF NOT EXISTS basic_demo;

-- Customers table
CREATE TABLE basic_demo.customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE basic_demo.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES basic_demo.customers(customer_id),
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_basic_customers_email ON basic_demo.customers(email);
CREATE INDEX idx_basic_customers_created_at ON basic_demo.customers(created_at);
CREATE INDEX idx_basic_orders_customer_id ON basic_demo.orders(customer_id);
CREATE INDEX idx_basic_orders_order_date ON basic_demo.orders(order_date);
