-- ============================================
-- SUPPRESSION DES DONNÉES INVALIDES
-- ============================================
-- Objectif : conserver uniquement les données valides dans les tables demo.*

-- 1. CUSTOMERS
DELETE FROM `demo.customers`
WHERE customer_id BETWEEN 200 AND 202     -- doublons
   OR customer_id BETWEEN 400 AND 403     -- nulls
   OR customer_id BETWEEN 600 AND 605     -- emails invalides
   OR customer_id BETWEEN 14000 AND 14005 -- ages hors plage
;

-- 2. ORDERS
DELETE FROM `demo.orders`
WHERE order_id BETWEEN 8000 AND 8003      -- clés orphelines
   OR order_id BETWEEN 10000 AND 10003    -- dates futures
   OR order_id BETWEEN 12000 AND 12003    -- statuts invalides
   OR order_id BETWEEN 16000 AND 16003    -- données trop anciennes
   OR order_id BETWEEN 20000 AND 20050;   -- pic anormal


-- 3. CUSTOMER_DATAMART
DELETE FROM `demo.customer_datamart`
WHERE customer_id BETWEEN 18000 AND 18100 -- distribution anormale
   OR customer_id BETWEEN 22000 AND 22010; -- trop de VIP buyers

-- 4. USER_SESSIONS
DELETE FROM `demo.user_sessions`
WHERE session_id BETWEEN 40000 AND 40003; -- sessions invalides (page_views < 1)

-- ============================================
-- VÉRIFICATION APRÈS SUPPRESSION
-- ============================================
SELECT 
    'Customers restants' AS table_name, COUNT(*) AS count 
FROM `demo.customers`

UNION ALL

SELECT 
    'Orders restants', COUNT(*) 
FROM `demo.orders`

UNION ALL

SELECT 
    'Customer_datamart restants', COUNT(*) 
FROM `demo.customer_datamart`

UNION ALL

SELECT 
    'User_sessions restants', COUNT(*) 
FROM `demo.user_sessions`;
