TRUNCATE TABLE demo.customers;
TRUNCATE TABLE demo.orders;
TRUNCATE TABLE demo.user_sessions;
TRUNCATE TABLE demo.customer_datamart;

-- ============================================
-- BIGQUERY - DONNÉES VALIDES (REFACTORISÉ)
-- ============================================
-- Utilisation: bq query --use_legacy_sql=false < bigquery_valid_data.sql

-- ============================================
-- 1. TABLE CUSTOMERS
-- ============================================

-- 1.1 UNIQUE TEST - Pas de doublons
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(100, 'unique1@email.com', 'Valid', 'User1', 25, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 DAY)),
(101, 'unique2@email.com', 'Valid', 'User2', 30, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 9 DAY)),
(102, 'unique3@email.com', 'Valid', 'User3', 35, 'active', 'Canada', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 8 DAY));

-- 1.2 NOT_NULL TEST - Pas de nulls
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(300, 'valid1@email.com', 'NotNull', 'User1', 28, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(301, 'valid2@email.com', 'NotNull', 'User2', 32, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 DAY));

-- 1.3 EMAIL_FORMAT TEST - Formats corrects
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(500, 'valid.user@company.com', 'Email', 'Valid1', 25, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY)),
(501, 'another+tag@domain.co.uk', 'Email', 'Valid2', 30, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY));

-- 1.4 RELATIONSHIP TEST - Customers de référence
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(700, 'ref1@email.com', 'Ref', 'User1', 25, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 DAY)),
(701, 'ref2@email.com', 'Ref', 'User2', 30, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY));

-- 1.5 RANGE_CHECK TEST - Ages valides [18-120]
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(13000, 'range1@email.com', 'Range', 'User1', 18, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(13001, 'range2@email.com', 'Range', 'User2', 65, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(13002, 'range3@email.com', 'Range', 'User3', 120, 'active', 'Canada', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY));

--- ============================================
-- 2. TABLE ORDERS
-- ============================================

-- 2.1 RELATIONSHIP TEST - Orders avec références valides
INSERT INTO `demo.orders` (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(7000, 700, DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY), CAST(150.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(7001, 701, DATE_SUB(CURRENT_DATE(), INTERVAL 4 DAY), CAST(200.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 DAY));

-- 2.2 FUTURE_DATE TEST - Dates passées
INSERT INTO `demo.orders` (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(9000, 100, DATE_SUB(CURRENT_DATE(), INTERVAL 10 DAY), CAST(150.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 DAY)),
(9001, 101, DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY), CAST(200.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(9002, 102, CURRENT_DATE(), CAST(100.00 AS NUMERIC), 'completed', CURRENT_TIMESTAMP());

-- 2.3 ACCEPTED_VALUES TEST - Statuts valides
INSERT INTO `demo.orders` (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(11000, 300, DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY), CAST(150.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(11001, 301, DATE_SUB(CURRENT_DATE(), INTERVAL 4 DAY), CAST(200.00 AS NUMERIC), 'pending', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 DAY)),
(11002, 300, DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), CAST(100.00 AS NUMERIC), 'cancelled', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY));

-- 2.4 FRESHNESS TEST - Données < 2 jours
INSERT INTO `demo.orders` (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(15000, 500, CURRENT_DATE(), CAST(150.00 AS NUMERIC), 'completed', CURRENT_TIMESTAMP()),
(15001, 501, DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY), CAST(200.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)),
(15002, 500, DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY), CAST(100.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY));


-- 2.5 STATISTICAL_THRESHOLD - Pattern normal (~7 orders/jour)
INSERT INTO `demo.orders` (order_id, customer_id, order_date, total_amount, status, created_at)
WITH days AS (
    SELECT day FROM UNNEST(GENERATE_ARRAY(1, 10)) AS day
),
order_rows AS (
    SELECT order_row FROM UNNEST(GENERATE_ARRAY(1, 7)) AS order_row
),
customers AS (
    SELECT ARRAY_AGG(customer_id) AS customer_ids
    FROM UNNEST([100, 101, 102, 300, 301]) AS customer_id
)
SELECT 
    19000 + (day * 10) + order_row AS order_id,
    customer_ids[OFFSET(MOD(order_row, 5))] AS customer_id,
    DATE_SUB(CURRENT_DATE(), INTERVAL day DAY) AS order_date,
    CAST(100.00 + (order_row * 20) AS NUMERIC) AS total_amount,
    'completed' AS status,
    TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL day DAY) AS created_at
FROM days, order_rows, customers;


-- ============================================
-- 3. TABLE CUSTOMER_DATAMART
-- ============================================

-- 3.1 ACCEPTED_BENCHMARK - 50 Mono-buyers (50%)
INSERT INTO `demo.customer_datamart` (customer_id, country, lifetime_value, order_frequency, customer_segment)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 50)) AS num
)
SELECT 
    17000 + num as customer_id,
    'USA' as country,
    100 + num as lifetime_value,
    1 as order_frequency,
    'Mono-buyer' as customer_segment
FROM numbers;

-- 3.2 ACCEPTED_BENCHMARK - 40 Regular-buyers (40%)
INSERT INTO `demo.customer_datamart` (customer_id, country, lifetime_value, order_frequency, customer_segment)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 40)) AS num
)
SELECT 
    17050 + num as customer_id,
    'UK' as country,
    500 + (num * 10) as lifetime_value,
    5 + MOD(num, 15) as order_frequency,
    'Regular-buyer' as customer_segment
FROM numbers;

-- 3.3 ACCEPTED_BENCHMARK - 10 VIP-buyers (10%)
INSERT INTO `demo.customer_datamart` (customer_id, country, lifetime_value, order_frequency, customer_segment)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 10)) AS num
)
SELECT 
    17090 + num as customer_id,
    'France' as country,
    5000 + (num * 100) as lifetime_value,
    25 + num as order_frequency,
    'VIP-buyer' as customer_segment
FROM numbers;

-- 3.4 CUSTOM_SQL TEST - Exactement 5 VIP (limite acceptable)
INSERT INTO `demo.customer_datamart` (customer_id, country, lifetime_value, order_frequency, customer_segment) VALUES
(21001, 'USA', 5000, 25, 'VIP-buyer'),
(21002, 'UK', 4500, 30, 'VIP-buyer'),
(21003, 'France', 6000, 35, 'VIP-buyer'),
(21004, 'Germany', 5500, 28, 'VIP-buyer'),
(21005, 'Spain', 4800, 32, 'VIP-buyer');

-- ============================================
-- 4. TABLE USER_SESSIONS
-- ============================================

-- 4.1 RANGE_CHECK - Sessions valides (page_views >= 1)
INSERT INTO `demo.user_sessions` (session_id, session_date, user_id, page_views, created_at)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 20)) AS num
)
SELECT 
    30000 + num as session_id,
    DATE_SUB(CURRENT_DATE(), INTERVAL MOD(num, 5) DAY) as session_date,
    1 + MOD(num, 4) as user_id,
    3 + MOD(num, 7) as page_views,
    TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL MOD(num, 5) DAY) as created_at
FROM numbers;

-- ============================================
-- VÉRIFICATIONS
-- ============================================

SELECT 
    'Customers valides' as table_name, 
    COUNT(*) as count 
FROM `demo.customers` 
WHERE customer_id BETWEEN 100 AND 13002

UNION ALL

SELECT 
    'Orders valides', 
    COUNT(*) 
FROM `demo.orders` 
WHERE order_id BETWEEN 7000 AND 19999

UNION ALL

SELECT 
    'Customer_datamart valides', 
    COUNT(*) 
FROM `demo.customer_datamart` 
WHERE customer_id BETWEEN 17001 AND 21005

UNION ALL

SELECT 
    'User_sessions valides', 
    COUNT(*) 
FROM `demo.user_sessions` 
WHERE session_id BETWEEN 30000 AND 30020;