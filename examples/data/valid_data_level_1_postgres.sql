-- ============================================
-- POSTGRESQL - DONNÉES VALIDES (REFACTORISÉ)
-- ============================================
CREATE TABLE demo.customer_datamart (
    customer_id       INT PRIMARY KEY,
    country            VARCHAR(100),
    lifetime_value     NUMERIC(12, 2),
    order_frequency    INT,
    customer_segment   VARCHAR(50),
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

TRUNCATE TABLE demo.customers RESTART IDENTITY CASCADE;
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;
TRUNCATE TABLE demo.user_sessions RESTART IDENTITY CASCADE;
TRUNCATE TABLE demo.customer_datamart RESTART IDENTITY CASCADE;

-- ============================================
-- 1. TABLE CUSTOMERS
-- ============================================

-- 1.1 UNIQUE TEST - Pas de doublons
INSERT INTO demo.customers (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(100, 'unique1@email.com', 'Valid', 'User1', 25, 'active', 'USA', NOW() - INTERVAL '10 days'),
(101, 'unique2@email.com', 'Valid', 'User2', 30, 'active', 'UK', NOW() - INTERVAL '9 days'),
(102, 'unique3@email.com', 'Valid', 'User3', 35, 'active', 'Canada', NOW() - INTERVAL '8 days');

-- 1.2 NOT_NULL TEST
INSERT INTO demo.customers VALUES
(300, 'valid1@email.com', 'NotNull', 'User1', 28, 'active', 'USA', NOW() - INTERVAL '5 days'),
(301, 'valid2@email.com', 'NotNull', 'User2', 32, 'active', 'UK', NOW() - INTERVAL '4 days');
 
-- 1.3 EMAIL_FORMAT TEST
INSERT INTO demo.customers VALUES
(500, 'valid.user@company.com', 'Email', 'Valid1', 25, 'active', 'USA', NOW() - INTERVAL '2 days'),
(501, 'another+tag@domain.co.uk', 'Email', 'Valid2', 30, 'active', 'UK', NOW() - INTERVAL '2 days');

-- 1.4 RELATIONSHIP TEST
INSERT INTO demo.customers VALUES
(700, 'ref1@email.com', 'Ref', 'User1', 25, 'active', 'USA', NOW() - INTERVAL '15 days'),
(701, 'ref2@email.com', 'Ref', 'User2', 30, 'active', 'UK', NOW() - INTERVAL '14 days');

-- 1.5 RANGE_CHECK TEST
INSERT INTO demo.customers VALUES
(13000, 'range1@email.com', 'Range', 'User1', 18, 'active', 'USA', NOW() - INTERVAL '5 days'),
(13001, 'range2@email.com', 'Range', 'User2', 65, 'active', 'UK', NOW() - INTERVAL '5 days'),
(13002, 'range3@email.com', 'Range', 'User3', 120, 'active', 'Canada', NOW() - INTERVAL '5 days');


-- ============================================
-- 2. TABLE ORDERS
-- ============================================

-- 2.1 RELATIONSHIP TEST
INSERT INTO demo.orders VALUES
(7000, 700, CURRENT_DATE - INTERVAL '5 days', 150.00, 'completed', NOW() - INTERVAL '5 days'),
(7001, 701, CURRENT_DATE - INTERVAL '4 days', 200.00, 'completed', NOW() - INTERVAL '4 days');

-- 2.2 FUTURE_DATE TEST
INSERT INTO demo.orders VALUES
(9000, 100, CURRENT_DATE - INTERVAL '10 days', 150.00, 'completed', NOW() - INTERVAL '10 days'),
(9001, 101, CURRENT_DATE - INTERVAL '5 days', 200.00, 'completed', NOW() - INTERVAL '5 days'),
(9002, 102, CURRENT_DATE, 100.00, 'completed', NOW());

-- 2.3 ACCEPTED_VALUES TEST
INSERT INTO demo.orders VALUES
(11000, 300, CURRENT_DATE - INTERVAL '5 days', 150.00, 'completed', NOW() - INTERVAL '5 days'),
(11001, 301, CURRENT_DATE - INTERVAL '4 days', 200.00, 'pending', NOW() - INTERVAL '4 days'),
(11002, 300, CURRENT_DATE - INTERVAL '3 days', 100.00, 'cancelled', NOW() - INTERVAL '3 days');

-- 2.4 FRESHNESS TEST
INSERT INTO demo.orders VALUES
(15000, 500, CURRENT_DATE, 150.00, 'completed', NOW()),
(15001, 501, CURRENT_DATE - INTERVAL '2 day', 200.00, 'completed', NOW() - INTERVAL '1 day'),
(15002, 500, CURRENT_DATE - INTERVAL '2 days', 100.00, 'completed', NOW() - INTERVAL '2 days');

-- 2.5 STATISTICAL_THRESHOLD TEST   
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at)
SELECT 
    19000 + (d.day * 10) + o.order_row AS order_id,
    c.customer_id,
    CURRENT_DATE - (d.day || ' days')::interval AS order_date,
    100.00 + (o.order_row * 20) AS total_amount,
    'completed' AS status,
    NOW() - (d.day || ' days')::interval AS created_at
FROM generate_series(1, 10) AS d(day)
CROSS JOIN generate_series(1, 7) AS o(order_row)
CROSS JOIN (SELECT unnest(array[100, 101, 102, 300, 301]) AS customer_id) c;


-- ============================================
-- 3. TABLE CUSTOMER_DATAMART
-- ============================================

-- 3.1 MONO-BUYERS
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 
    17000 + num,
    'USA',
    100 + num,
    1,
    'Mono-buyer'
FROM generate_series(1, 50) AS g(num);

-- 3.2 REGULAR-BUYERS
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 
    17050 + num,
    'UK',
    500 + (num * 10),
    5 + (num % 15),
    'Regular-buyer'
FROM generate_series(1, 40) AS g(num);

-- 3.3 VIP-BUYERS
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 
    17090 + num,
    'France',
    5000 + (num * 100),
    25 + num,
    'VIP-buyer'
FROM generate_series(1, 10) AS g(num);

-- 3.4 CUSTOM_SQL TEST
INSERT INTO demo.customer_datamart VALUES
(21001, 'USA', 5000, 25, 'VIP-buyer'),
(21002, 'UK', 4500, 30, 'VIP-buyer'),
(21003, 'France', 6000, 35, 'VIP-buyer'),
(21004, 'Germany', 5500, 28, 'VIP-buyer'),
(21005, 'Spain', 4800, 32, 'VIP-buyer');


-- ============================================
-- 4. TABLE USER_SESSIONS
-- ============================================

INSERT INTO demo.user_sessions (session_id, session_date, user_id, page_views, created_at)
SELECT 
    30000 + num,
    CURRENT_DATE - (num % 5 || ' days')::interval,
    1 + (num % 4),
    3 + (num % 7),
    NOW() - (num % 5 || ' days')::interval
FROM generate_series(1, 20) AS g(num);


-- ============================================
-- VÉRIFICATIONS
-- ============================================

SELECT 'Customers valides' AS table_name, COUNT(*) AS count 
FROM demo.customers 
WHERE customer_id BETWEEN 100 AND 13002

UNION ALL

SELECT 'Orders valides', COUNT(*) 
FROM demo.orders 
WHERE order_id BETWEEN 7000 AND 19999

UNION ALL

SELECT 'Customer_datamart valides', COUNT(*) 
FROM demo.customer_datamart 
WHERE customer_id BETWEEN 17001 AND 21005

UNION ALL

SELECT 'User_sessions valides', COUNT(*) 
FROM demo.user_sessions 
WHERE session_id BETWEEN 30000 AND 30020;
--- Another verifications;



SELECT 'Customers valides' AS table_name, COUNT(*) AS count 
FROM demo.customers

UNION ALL

SELECT 'Orders valides', COUNT(*) 
FROM demo.orders 


UNION ALL

SELECT 'Customer_datamart valides', COUNT(*) 
FROM demo.customer_datamart 

UNION ALL

SELECT 'User_sessions valides', COUNT(*) 
FROM demo.user_sessions 
-- Fin du script