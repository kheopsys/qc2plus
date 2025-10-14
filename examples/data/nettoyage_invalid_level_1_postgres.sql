-- ============================================
-- SUPPRESSION DES DONNÉES INVALIDES - POSTGRESQL
-- ============================================
-- Objectif : conserver uniquement les données valides
-- Base de données : demo
-- Les tables concernées : customers, orders, customer_datamart, user_sessions
DELETE FROM demo.customers
WHERE customer_id BETWEEN 10000 AND 405     -- nulls  

DELETE FROM demo.orders
WHERE order_id BETWEEN 20001 AND 20049;   -- pic anormal;


-- 1️⃣ TABLE CUSTOMERS
DELETE FROM demo.customers
WHERE customer_id BETWEEN 200 AND 202     -- doublons
   OR customer_id BETWEEN 400 AND 403     -- nulls
   OR customer_id BETWEEN 600 AND 605     -- emails invalides
   OR customer_id BETWEEN 14000 AND 14005 -- ages hors plage
;

-- 2️⃣ TABLE ORDERS
DELETE FROM demo.orders
WHERE order_id BETWEEN 8000 AND 8003      -- clés orphelines
   OR order_id BETWEEN 10000 AND 10003    -- dates futures
   OR order_id BETWEEN 12000 AND 12003    -- statuts invalides
   OR order_id BETWEEN 16000 AND 16003    -- données trop anciennes
   OR order_id BETWEEN 20000 AND 20050;   -- pic anormal
;

-- 3️⃣ TABLE CUSTOMER_DATAMART
DELETE FROM demo.customer_datamart
WHERE customer_id BETWEEN 18000 AND 18100 -- distribution anormale
   OR customer_id BETWEEN 22000 AND 22010; -- trop de VIP buyers
;

-- 4️⃣ TABLE USER_SESSIONS
DELETE FROM demo.user_sessions
WHERE session_id BETWEEN 40000 AND 40003; -- sessions invalides (page_views < 1)
;

-- ============================================
-- VÉRIFICATION APRÈS SUPPRESSION
-- ============================================
-- Vérifie combien de lignes valides restent dans chaque table

SELECT 
    'customers' AS table_name, COUNT(*) AS remaining_rows 
FROM demo.customers

UNION ALL

SELECT 
    'orders' AS table_name, COUNT(*) 
FROM demo.orders

UNION ALL

SELECT 
    'customer_datamart' AS table_name, COUNT(*) 
FROM demo.customer_datamart

UNION ALL

SELECT 
    'user_sessions' AS table_name, COUNT(*) 
FROM demo.user_sessions;
