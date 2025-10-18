

-- ============================================
-- FICHIER 1: DONNÉES VALIDES (VERSION DÉTERMINISTE)
-- Distribution PARFAITEMENT stable entre les deux périodes
-- ============================================

-- Nettoyer d'abord
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- ============================================
-- PÉRIODE DE RÉFÉRENCE (J-120 à J-31)
-- Distribution EXACTE: pending=10%, completed=80%, cancelled=10%
-- Total: 1000 commandes
-- ============================================

-- Pending: Exactement 100 commandes (10%)
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1 as customer_id,
    CURRENT_DATE - (60 + (i % 30))::integer as order_date,
    150 + (i % 100) as total_amount,  -- Entre 150€ et 249€
    'pending' as status,
    CURRENT_DATE - (60 + (i % 30))::integer as created_at
FROM generate_series(1, 100) as i;

-- Completed: Exactement 800 commandes (80%)
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1 as customer_id,
    CURRENT_DATE - (60 + (i % 30))::integer as order_date,
    150 + (i % 100) as total_amount,  -- Entre 150€ et 249€
    'completed' as status,
    CURRENT_DATE - (60 + (i % 30))::integer as created_at
FROM generate_series(1, 800) as i;

-- Cancelled: Exactement 100 commandes (10%)
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1 as customer_id,
    CURRENT_DATE - (60 + (i % 30))::integer as order_date,
    150 + (i % 100) as total_amount,  -- Entre 150€ et 249€
    'cancelled' as status,
    CURRENT_DATE - (60 + (i % 30))::integer as created_at
FROM generate_series(1, 100) as i;

-- ============================================
-- PÉRIODE DE COMPARAISON (J-30 à aujourd'hui)
-- Distribution IDENTIQUE: pending=10%, completed=80%, cancelled=10%
-- Total: 1000 commandes
-- ============================================

-- Pending: Exactement 100 commandes (10%)
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1 as customer_id,
    CURRENT_DATE - (i % 30)::integer as order_date,
    150 + (i % 100) as total_amount,  -- MÊME distribution de prix
    'pending' as status,
    CURRENT_DATE - (i % 30)::integer as created_at
FROM generate_series(1, 100) as i;

-- Completed: Exactement 800 commandes (80%)
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1 as customer_id,
    CURRENT_DATE - (i % 30)::integer as order_date,
    150 + (i % 100) as total_amount,  -- MÊME distribution de prix
    'completed' as status,
    CURRENT_DATE - (i % 30)::integer as created_at
FROM generate_series(1, 800) as i;

-- Cancelled: Exactement 100 commandes (10%)
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1 as customer_id,
    CURRENT_DATE - (i % 30)::integer as order_date,
    150 + (i % 100) as total_amount,  -- MÊME distribution de prix
    'cancelled' as status,
    CURRENT_DATE - (i % 30)::integer as created_at
FROM generate_series(1, 100) as i;

-- ============================================
-- Vérification
-- ============================================
SELECT 
    '📊 REFERENCE PERIOD' as period,
    status,
    COUNT(*) as count,
    ROUND(AVG(total_amount), 2) as avg_amount,
    ROUND(SUM(total_amount), 2) as total_revenue,
    ROUND(COUNT(*) * 100.0 / 1000.0, 1) as percentage
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '120 days'
  AND order_date < CURRENT_DATE - INTERVAL '30 days'
GROUP BY status

UNION ALL

SELECT 
    '📊 COMPARISON PERIOD' as period,
    status,
    COUNT(*) as count,
    ROUND(AVG(total_amount), 2) as avg_amount,
    ROUND(SUM(total_amount), 2) as total_revenue,
    ROUND(COUNT(*) * 100.0 / 1000.0, 1) as percentage
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status
ORDER BY period DESC, status;

-- ✅ Résultat attendu:
-- REFERENCE:  pending=100 (10%), completed=800 (80%), cancelled=100 (10%)
-- COMPARISON: pending=100 (10%), completed=800 (80%), cancelled=100 (10%)
-- → Test: passed=True, anomalies_count=0