-- ============================================
-- 1. TABLE CUSTOMERS
-- ============================================
-- 1.1 UNIQUE TEST - 3 doublons (6 lignes → 3 doublons détectés)
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(200, 'dup1@email.com', 'Dup', 'User1', 28, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(200, 'dup2@email.com', 'Dup', 'User2', 32, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),      -- DOUBLON
(201, 'dup3@email.com', 'Dup', 'User3', 40, 'active', 'France', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(201, 'dup4@email.com', 'Dup', 'User4', 45, 'active', 'Germany', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)), -- DOUBLON
(202, 'dup5@email.com', 'Dup', 'User5', 35, 'active', 'Spain', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),
(202, 'dup6@email.com', 'Dup', 'User6', 38, 'active', 'Italy', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY));   -- DOUBLON
-- Attendu: failed_rows = 3 doublons

-- 1.2 NOT_NULL TEST - 4 valeurs NULL
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(400, 'dup6@email.com', 'Null', 'User1', 28, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),     -- NULL
(401, 'dup6@email.com', 'Null', 'User2', 32, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),      -- NULL
(402, 'dup6@email.com', 'Null', 'User3', 35, 'active', 'France', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),  -- NULL
(403, 'dup6@email.com', 'Null', 'User4', 40, 'active', 'Germany', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)); -- NULL
-- Attendu: failed_rows = 4 nulls


-- 1.3 EMAIL_FORMAT TEST - 6 formats invalides
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(600, 'invalid-email', 'Invalid', 'User1', 28, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),          -- Pas de @
(601, 'missing.domain@', 'Invalid', 'User2', 32, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),         -- Pas de domaine
(602, '@nodomain.com', 'Invalid', 'User3', 35, 'active', 'France', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),       -- Pas de partie locale
(603, 'spaces in@email.com', 'Invalid', 'User4', 40, 'active', 'Germany', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)), -- Espaces
(604, 'double@@domain.com', 'Invalid', 'User5', 45, 'active', 'Spain', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),   -- Double @
(605, 'nodot@domaincom', 'Invalid', 'User6', 50, 'active', 'Italy', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY));      -- Pas de point
-- Attendu: failed_rows = 6 emails invalides

-- 1.4 RANGE_CHECK TEST - 6 ages hors plage [18-120]
INSERT INTO `demo.customers` (customer_id, email, first_name, last_name, age, status, country, created_at) VALUES
(14000, 'inv1@email.com', 'Invalid', 'User1', 10, 'active', 'USA', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),    -- < 18
(14001, 'inv2@email.com', 'Invalid', 'User2', 15, 'active', 'UK', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),     -- < 18
(14002, 'inv3@email.com', 'Invalid', 'User3', 150, 'active', 'France', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)), -- > 120
(14003, 'inv4@email.com', 'Invalid', 'User4', 200, 'active', 'Germany', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),-- > 120
(14004, 'inv5@email.com', 'Invalid', 'User5', -5, 'active', 'Spain', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),   -- Négatif
(14005, 'inv6@email.com', 'Invalid', 'User6', 0, 'active', 'Italy', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY));    -- < 18
-- Attendu: failed_rows = 6 hors plage



-- ============================================
-- 2. TABLE ORDERS - DONNÉES INVALIDES
-- ============================================

-- 2.1 RELATIONSHIP TEST - 4 clés orphelines (customer_id inexistants)
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(8000, 999998, DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY), CAST(150.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)), -- Orphelin
(8001, 999997, DATE_SUB(CURRENT_DATE(), INTERVAL 4 DAY), CAST(200.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 DAY)), -- Orphelin
(8002, 999996, DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), CAST(180.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY)), -- Orphelin
(8003, 999995, DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY), CAST(220.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY)); -- Orphelin
-- Attendu: failed_rows = 4 orphelins

-- 2.2 FUTURE_DATE TEST - 4 dates futures
INSERT INTO demo.orders (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(10000, 1, DATE_ADD(CURRENT_DATE(), INTERVAL 5 DAY), CAST(150.00 AS NUMERIC), 'pending', CURRENT_TIMESTAMP()),   -- +5 jours
(10001, 1, DATE_ADD(CURRENT_DATE(), INTERVAL 10 DAY), CAST(200.00 AS NUMERIC), 'pending', CURRENT_TIMESTAMP()),  -- +10 jours
(10002, 1, DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY), CAST(180.00 AS NUMERIC), 'pending', CURRENT_TIMESTAMP()),  -- +30 jours
(10003, 1, DATE_ADD(CURRENT_DATE(), INTERVAL 60 DAY), CAST(220.00 AS NUMERIC), 'pending', CURRENT_TIMESTAMP());  -- +60 jours

-- Attendu: failed_rows = 4 dates futures

-- 2.3 ACCEPTED_VALUES TEST - 4 statuts invalides
INSERT INTO `demo.orders` (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(12000, 1, DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY), CAST(150.00 AS NUMERIC), 'shipped', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),     -- Invalide
(12001, 1, DATE_SUB(CURRENT_DATE(), INTERVAL 4 DAY), CAST(200.00 AS NUMERIC), 'processing', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 DAY)), -- Invalide
(12002, 1, DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), CAST(180.00 AS NUMERIC), 'returned', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY)),   -- Invalide
(12003, 1, DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY), CAST(220.00 AS NUMERIC), 'refunded', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY));   -- Invalide
-- Attendu: failed_rows = 4 statuts invalides (valeurs autorisées: completed, pending, cancelled)

-- 2.4 FRESHNESS TEST - 4 données trop anciennes (> 2 jours)
INSERT INTO `demo.orders` (order_id, customer_id, order_date, total_amount, status, created_at) VALUES
(16000, 1, DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY), CAST(150.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),   -- -5 jours TROP VIEUX
(16001, 1, DATE_SUB(CURRENT_DATE(), INTERVAL 10 DAY), CAST(200.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 DAY)), -- -10 jours TROP VIEUX
(16002, 1, DATE_SUB(CURRENT_DATE(), INTERVAL 15 DAY), CAST(180.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 15 DAY)), -- -15 jours TROP VIEUX
(16003, 1, DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY), CAST(220.00 AS NUMERIC), 'completed', TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)); -- -30 jours TROP VIEUX
-- Attendu: failed_rows = 4 (max_age_days = 2)

-- 2.5 STATISTICAL_THRESHOLD - Pic anormal (50 orders vs baseline ~7)
INSERT INTO `demo.orders` (order_id, customer_id, order_date, total_amount, status, created_at)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 50)) AS num
)
SELECT 
    20000 + num as order_id,
    1 as customer_id,
    CURRENT_DATE() as order_date,
    CAST(100.00 + (num * 10) AS NUMERIC) as total_amount,
    'completed' as status,
    CURRENT_TIMESTAMP() as created_at
FROM numbers;
-- Attendu: Spike détecté (50 orders aujourd'hui vs moyenne de 7/jour)


-- ============================================
-- 3. TABLE CUSTOMER_DATAMART - DONNÉES INVALIDES
-- ============================================

-- 3.1 ACCEPTED_BENCHMARK - Distribution anormale 20/30/50 (au lieu de 50/40/10)

-- 20 Mono-buyers (20% au lieu de 50% attendu) - ÉCART DE 30%
INSERT INTO `demo.customer_datamart` (customer_id, country, lifetime_value, order_frequency, customer_segment)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 20)) AS num
)
SELECT 
    18000 + num as customer_id,
    'USA' as country,
    100 as lifetime_value,
    1 as order_frequency,
    'Mono-buyer' as customer_segment
FROM numbers;

-- 30 Regular-buyers (30% au lieu de 40% attendu) - ÉCART DE 10% (acceptable)
INSERT INTO `demo.customer_datamart` (customer_id, country, lifetime_value, order_frequency, customer_segment)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 30)) AS num
)
SELECT 
    18020 + num as customer_id,
    'UK' as country,
    500 as lifetime_value,
    5 as order_frequency,
    'Regular-buyer' as customer_segment
FROM numbers;

-- 50 VIP-buyers (50% au lieu de 10% attendu) - ÉCART DE 40% ⚠️ CRITIQUE
INSERT INTO `demo.customer_datamart` (customer_id, country, lifetime_value, order_frequency, customer_segment)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 50)) AS num
)
SELECT 
    18050 + num as customer_id,
    'France' as country,
    5000 as lifetime_value,
    25 as order_frequency,
    'VIP-buyer' as customer_segment
FROM numbers;
-- Attendu: Distribution VIP = 50% au lieu de 10% (écart > threshold 20%)

-- 3.2 CUSTOM_SQL TEST - 10 VIP buyers (> 5 limite)
INSERT INTO `demo.customer_datamart` (customer_id, country, lifetime_value, order_frequency, customer_segment)
WITH numbers AS (
    SELECT num FROM UNNEST(GENERATE_ARRAY(1, 10)) AS num
)
SELECT 
    22000 + num as customer_id,
    'USA' as country,
    5000 as lifetime_value,
    25 as order_frequency,
    'VIP-buyer' as customer_segment
FROM numbers;
-- Attendu: COUNT(VIP-buyer) = 10 > 5 (limite autorisée)

-- ============================================
-- 4. TABLE USER_SESSIONS - DONNÉES INVALIDES
-- ============================================

-- 4.1 RANGE_CHECK - 4 sessions invalides (page_views < 1)
INSERT INTO `demo.user_sessions` (session_id, session_date, user_id, page_views, created_at) VALUES
(40000, DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY), 1, 0, TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 DAY)),    -- 0 pages
(40001, DATE_SUB(CURRENT_DATE(), INTERVAL 4 DAY), 2, -1, TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 DAY)),   -- Négatif
(40002, DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY), 3, 0, TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY)),    -- 0 pages
(40003, DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY), 4, -5, TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY));   -- Négatif
-- Attendu: failed_rows = 4 (min_value = 1)
