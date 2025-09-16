
-- Basic demo schema and tables
CREATE SCHEMA IF NOT EXISTS demo;

-- Customers table
CREATE TABLE demo.customers (
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
CREATE TABLE demo.orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS demo.user_sessions (
    session_id SERIAL PRIMARY KEY,
    session_date DATE NOT NULL,
    user_id INTEGER NOT NULL,
    page_views INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

