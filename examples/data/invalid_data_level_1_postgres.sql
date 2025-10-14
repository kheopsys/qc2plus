-- ============================================
-- 1. TABLE CUSTOMERS
-- ============================================

-- 1.1 UNIQUE TEST - 3 doublons (6 lignes → 3 doublons détectés)
INSERT INTO demo.customers (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(200, 'dup1@email.com', 'Dup', 'User1', 28, 'active', 'USA', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(200, 'dup2@email.com', 'Dup', 'User2', 32, 'active', 'UK', CURRENT_TIMESTAMP - INTERVAL '5 days'),      -- DOUBLON
(201, 'dup3@email.com', 'Dup', 'User3', 40, 'active', 'France', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(201, 'dup4@email.com', 'Dup', 'User4', 45, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days'), -- DOUBLON
(202, 'dup5@email.com', 'Dup', 'User5', 35, 'active', 'Spain', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(202, 'dup6@email.com', 'Dup', 'User6', 38, 'active', 'Italy', CURRENT_TIMESTAMP - INTERVAL '5 days');   -- DOUBLON
-- Attendu: failed_rows = 3 doublons


-- 1.2 NOT_NULL TEST - 4 valeurs NULL
INSERT INTO demo.customers (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES

(400, 'dup6@email.com', NULL, 'User1', 28, 'active', 'USA', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(401, 'dup6@email.com', NULL, 'User2', 32, 'active', 'UK', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(402, 'dup6@email.com', NULL, 'User3', 35, 'active', 'France', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(403, 'dup6@email.com', NULL, 'User4', 40, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(404, 'dup10@email.com', NULL, 'User4', 40, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(405, 'dup10@email.com', NULL, 'User4', 40, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days');

-- Attendu: failed_rows = 4 nulls


-- 1.3 EMAIL_FORMAT TEST - 6 formats invalides
INSERT INTO demo.customers (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(600, 'invalid-email', 'Invalid', 'User1', 28, 'active', 'USA', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(601, 'missing.domain@', 'Invalid', 'User2', 32, 'active', 'UK', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(602, '@nodomain.com', 'Invalid', 'User3', 35, 'active', 'France', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(603, 'spaces in@email.com', 'Invalid', 'User4', 40, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(604, 'double@@domain.com', 'Invalid', 'User5', 45, 'active', 'Spain', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(605, 'nodot@domaincom', 'Invalid', 'User6', 50, 'active', 'Italy', CURRENT_TIMESTAMP - INTERVAL '5 days');
-- Attendu: failed_rows = 6 emails invalides
-- 1.4 RANGE_CHECK TEST - 6 ages hors plage [18-120]
INSERT INTO demo.customers (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(14000, 'inv1@email.com', 'Invalid', 'User1', 10, 'active', 'USA', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14001, 'inv2@email.com', 'Invalid', 'User2', 15, 'active', 'UK', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14002, 'inv3@email.com', 'Invalid', 'User3', 150, 'active', 'France', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14003, 'inv4@email.com', 'Invalid', 'User4', 200, 'active', 'Germany', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14004, 'inv5@email.com', 'Invalid', 'User5', -5, 'active', 'Spain', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(14005, 'inv6@email.com', 'Invalid', 'User6', 0, 'active', 'Italy', CURRENT_TIMESTAMP - INTERVAL '5 days');
-- Attendu: failed_rows = 6 hors plage


-- ============================================
-- 2. TABLE ORDERS - DONNÉES INVALIDES
-- ============================================

-- 2.1 RELATIONSHIP TEST - 4 clés orphelines (customer_id inexistants)
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(8000, 999998, CURRENT_DATE - INTERVAL '5 days', 150.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(8001, 999997, CURRENT_DATE - INTERVAL '4 days', 200.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '4 days'),
(8002, 999996, CURRENT_DATE - INTERVAL '3 days', 180.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '3 days'),
(8003, 999995, CURRENT_DATE - INTERVAL '2 days', 220.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '2 days');
-- Attendu: failed_rows = 4 orphelins


-- 2.2 FUTURE_DATE TEST - 4 dates futures
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(10000, 1, CURRENT_DATE + INTERVAL '5 days', 150.00, 'pending', CURRENT_TIMESTAMP),
(10001, 1, CURRENT_DATE + INTERVAL '10 days', 200.00, 'pending', CURRENT_TIMESTAMP),
(10002, 1, CURRENT_DATE + INTERVAL '30 days', 180.00, 'pending', CURRENT_TIMESTAMP),
(10003, 1, CURRENT_DATE + INTERVAL '60 days', 220.00, 'pending', CURRENT_TIMESTAMP);
-- Attendu: failed_rows = 4 dates futures


-- 2.3 ACCEPTED_VALUES TEST - 4 statuts invalides
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(12000, 1, CURRENT_DATE - INTERVAL '5 days', 150.00, 'shipped', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(12001, 1, CURRENT_DATE - INTERVAL '4 days', 200.00, 'processing', CURRENT_TIMESTAMP - INTERVAL '4 days'),
(12002, 1, CURRENT_DATE - INTERVAL '3 days', 180.00, 'returned', CURRENT_TIMESTAMP - INTERVAL '3 days'),
(12003, 1, CURRENT_DATE - INTERVAL '2 days', 220.00, 'refunded', CURRENT_TIMESTAMP - INTERVAL '2 days');
-- Attendu: failed_rows = 4 statuts invalides


-- 2.4 FRESHNESS TEST - 4 données trop anciennes (> 2 jours)
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(16000, 1, CURRENT_DATE - INTERVAL '5 days', 150.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '5 days'),
(16001, 1, CURRENT_DATE - INTERVAL '10 days', 200.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '10 days'),
(16002, 1, CURRENT_DATE - INTERVAL '15 days', 180.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '15 days'),
(16003, 1, CURRENT_DATE - INTERVAL '30 days', 220.00, 'completed', CURRENT_TIMESTAMP - INTERVAL '30 days');
-- Attendu: failed_rows = 4 (max_age_days = 2)



-- 2.5 STATISTICAL_THRESHOLD TEST : Ajouter l'historique des 10 derniers jours
-- Version avec seulement 70 orders (7/jour sur 10 jours)
-- Ajouter 50 orders aujourd'hui pour créer une violation
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at)
SELECT 
    30000 + s.id AS order_id,
    100 AS customer_id,
    CURRENT_DATE AS order_date,
    100.00 + (s.id * 10) AS total_amount,
    'completed' AS status,
    CURRENT_TIMESTAMP AS created_at
FROM generate_series(1, 50) AS s(id);
-- Attendu: Spike détecté (50 orders aujourd'hui vs moyenne de 7/jour)


-- ============================================
-- 3. TABLE CUSTOMER_DATAMART - DONNÉES INVALIDES
-- ============================================

-- 3.1 ACCEPTED_BENCHMARK - Distribution anormale 20/30/50 (au lieu de 50/40/10)

-- 20 Mono-buyers
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 
    18000 + s.id,
    'USA',
    100,
    1,
    'Mono-buyer'
FROM generate_series(1, 20) AS s(id);

-- 30 Regular-buyers
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 
    18020 + s.id,
    'UK',
    500,
    5,
    'Regular-buyer'
FROM generate_series(1, 30) AS s(id);

-- 50 VIP-buyers
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 
    18050 + s.id,
    'France',
    5000,
    25,
    'VIP-buyer'
FROM generate_series(1, 50) AS s(id);


-- 3.2 CUSTOM_SQL TEST - 10 VIP buyers (> 5 limite)
INSERT INTO demo.customer_datamart (customer_id, country, lifetime_value, order_frequency, customer_segment)
SELECT 
    22000 + s.id,
    'USA',
    5000,
    25,
    'VIP-buyer'
FROM generate_series(1, 10) AS s(id);


-- ============================================
-- 4. TABLE USER_SESSIONS - DONNÉES INVALIDES
-- ============================================

-- 4.1 RANGE_CHECK - 4 sessions invalides (page_views < 1)
INSERT INTO demo.user_sessions (session_id, session_date, user_id, page_views, created_at) VALUES
(40000, CURRENT_DATE - INTERVAL '5 days', 1, 0, CURRENT_TIMESTAMP - INTERVAL '5 days'),
(40001, CURRENT_DATE - INTERVAL '4 days', 2, -1, CURRENT_TIMESTAMP - INTERVAL '4 days'),
(40002, CURRENT_DATE - INTERVAL '3 days', 3, 0, CURRENT_TIMESTAMP - INTERVAL '3 days'),
(40003, CURRENT_DATE - INTERVAL '2 days', 4, -5, CURRENT_TIMESTAMP - INTERVAL '2 days');

-- Attendu: failed_rows = 4 (min_value = 1)
-- ============================================