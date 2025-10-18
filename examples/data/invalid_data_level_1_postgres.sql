-- ============================================
-- 1. TABLE CUSTOMERS
-- ============================================

-- 1.1 NOT_NULL TEST - 4 valeurs NULL dans first_name
TRUNCATE TABLE demo.customers RESTART IDENTITY CASCADE;

INSERT INTO demo.customers (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(400, 'dup1@email.com', NULL, 'User1', 28, 'active', 'USA', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(401, 'dup2@email.com', NULL, 'User2', 32, 'active', 'UK', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(402, 'dup3@email.com', NULL, 'User3', 35, 'active', 'France', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(403, 'dup4@email.com', NULL, 'User4', 40, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(404, 'dup5@email.com', 'John', 'Valid', 30, 'active', 'USA', CURRENT_TIMESTAMP - INTERVAL '2 days'),
(405, 'dup6@email.com', 'Jane', 'Valid', 33, 'active', 'UK', CURRENT_TIMESTAMP - INTERVAL '1 day');

-- 🎯 Attendu: failed_rows = 4 NULLs sur first_name


-- 1.2 EMAIL_FORMAT TEST - 6 emails invalides
TRUNCATE TABLE demo.customers RESTART IDENTITY CASCADE;

INSERT INTO demo.customers (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(600, 'invalid-email', 'Invalid', 'User1', 28, 'active', 'USA', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(601, 'missing.domain@', 'Invalid', 'User2', 32, 'active', 'UK', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(602, '@nodomain.com', 'Invalid', 'User3', 35, 'active', 'France', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(603, 'spaces in@email.com', 'Invalid', 'User4', 40, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(604, 'double@@domain.com', 'Invalid', 'User5', 45, 'active', 'Spain', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(605, 'nodot@domaincom', 'Invalid', 'User6', 50, 'active', 'Italy', CURRENT_TIMESTAMP - INTERVAL '5 days');

-- 🎯 Attendu: failed_rows = 6 emails invalides


-- 1.3 RANGE_CHECK TEST - 6 âges hors plage [18-120]
TRUNCATE TABLE demo.customers RESTART IDENTITY CASCADE;

INSERT INTO demo.customers (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(14000, 'inv1@email.com', 'Invalid', 'User1', 10, 'active', 'USA', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14001, 'inv2@email.com', 'Invalid', 'User2', 15, 'active', 'UK', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14002, 'inv3@email.com', 'Invalid', 'User3', 150, 'active', 'France', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14003, 'inv4@email.com', 'Invalid', 'User4', 200, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14004, 'inv5@email.com', 'Invalid', 'User5', -5, 'active', 'Spain', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14005, 'inv6@email.com', 'Invalid', 'User6', 0, 'active', 'Italy', CURRENT_TIMESTAMP - INTERVAL '5 days');

-- 🎯 Attendu: failed_rows = 6 hors plage


-- ============================================
-- 2. TABLE ORDERS
-- ============================================

TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- 2.1 RELATIONSHIP TEST - 4 customer_id inexistants
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(8000, 999998, CURRENT_DATE - INTERVAL '5 days', 150.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(8001, 999997, CURRENT_DATE - INTERVAL '4 days', 200.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '4 days'),
(8002, 999996, CURRENT_DATE - INTERVAL '3 days', 180.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '3 days'),
(8003, 999995, CURRENT_DATE - INTERVAL '2 days', 220.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '2 days');

-- 🎯 Attendu: failed_rows = 4 clés orphelines


-- 2.2 FUTURE_DATE TEST - 4 dates futures
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(10000, 1, CURRENT_DATE + INTERVAL '5 days', 150.00, 'pending', CURRENT_TIMESTAMP),
(10001, 1, CURRENT_DATE + INTERVAL '10 days', 200.00, 'pending', CURRENT_TIMESTAMP),
(10002, 1, CURRENT_DATE + INTERVAL '30 days', 180.00, 'pending', CURRENT_TIMESTAMP),
(10003, 1, CURRENT_DATE + INTERVAL '60 days', 220.00, 'pending', CURRENT_TIMESTAMP);
-- 🎯 Attendu: failed_rows = 4 dates futures


-- 2.3 ACCEPTED_VALUES TEST - 4 statuts invalides
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(12000, 1, CURRENT_DATE - INTERVAL '5 days', 150.00, 'shipped', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(12001, 1, CURRENT_DATE - INTERVAL '4 days', 200.00, 'processing', CURRENT_TIMESTAMP - INTERVAL '4 days'),
(12002, 1, CURRENT_DATE - INTERVAL '3 days', 180.00, 'returned', CURRENT_TIMESTAMP - INTERVAL '3 days'),
(12003, 1, CURRENT_DATE - INTERVAL '2 days', 220.00, 'refunded', CURRENT_TIMESTAMP - INTERVAL '2 days');
-- 🎯 Attendu: failed_rows = 4 statuts invalides


-- 2.4 FRESHNESS TEST - données trop anciennes (> 2 jours)
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(16000, 1, CURRENT_DATE - INTERVAL '5 days', 150.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(16001, 1, CURRENT_DATE - INTERVAL '10 days', 200.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '10 days'),
(16002, 1, CURRENT_DATE - INTERVAL '15 days', 180.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '15 days'),
(16003, 1, CURRENT_DATE - INTERVAL '30 days', 220.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '30 days');
-- 🎯 Attendu: failed_rows = 4 (max_age_days = 2)


-- 2.5 STATISTICAL_THRESHOLD TEST : Historique stable + pic anormal
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- Étape 1 : Historique stable
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at)
SELECT
    10000 + s.id,
    (s.id % 1000) + 1,
    CURRENT_DATE - ((s.id % 30))::INT,
    100 + (RANDOM() * 20)::INT,
    'completed',
    CURRENT_TIMESTAMP - ((s.id % 30)) * INTERVAL '1 day'
FROM generate_series(1, 3000) AS s(id);

-- Étape 2 : Pic anormal aujourd’hui
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at)
SELECT
    20000 + s.id,
    (s.id % 1000) + 1,
    CURRENT_DATE,
    100 + (RANDOM() * 20)::INT,
    'completed',
    CURRENT_TIMESTAMP
FROM generate_series(1, 1000) AS s(id);
-- 🎯 Attendu: failed_rows > 0 (seuil statistique dépassé)


-- ============================================
-- 3. TABLE CUSTOMER_DATAMART
-- ============================================

TRUNCATE TABLE demo.customer_datamart RESTART IDENTITY CASCADE;

-- 3.1 ACCEPTED_BENCHMARK - Distribution anormale (20/30/50)
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 18000 + s.id, 'USA', 100, 1, 'Mono-buyer' FROM generate_series(1, 20) AS s(id);
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 18020 + s.id, 'UK', 500, 5, 'Regular-buyer' FROM generate_series(1, 30) AS s(id);
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 18050 + s.id, 'France', 5000, 25, 'VIP-buyer' FROM generate_series(1, 50) AS s(id);
-- 🎯 Attendu: failed_rows = 1 (écart à la distribution de référence 50/40/10)


-- 3.2 CUSTOM_SQL TEST - Trop de VIP buyers (> 10)
TRUNCATE TABLE demo.customer_datamart RESTART IDENTITY CASCADE;

INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 
    22000 + s.id,
    'USA',
    5000,
    25,
    'VIP-buyer'
FROM generate_series(1, 15) AS s(id);
-- 🎯 Attendu: failed_rows = 1 (10 VIP > limite de 5)


-- ============================================
-- 4. TABLE USER_SESSIONS
-- ============================================

TRUNCATE TABLE demo.user_sessions RESTART IDENTITY CASCADE;

-- 4.1 RANGE_CHECK - 4 sessions invalides (page_views < 1)
INSERT INTO demo.user_sessions (session_id, session_date, user_id, page_views, created_at) VALUES
(40000, CURRENT_DATE - INTERVAL '5 days', 1, 0, CURRENT_TIMESTAMP - INTERVAL '5 days'),
(40001, CURRENT_DATE - INTERVAL '4 days', 2, -1, CURRENT_TIMESTAMP - INTERVAL '4 days'),
(40002, CURRENT_DATE - INTERVAL '3 days', 3, 0, CURRENT_TIMESTAMP - INTERVAL '3 days'),
(40003, CURRENT_DATE - INTERVAL '2 days', 4, -5, CURRENT_TIMESTAMP - INTERVAL '2 days');
-- 🎯 Attendu: failed_rows = 4 (page_views < min_value = 1)
