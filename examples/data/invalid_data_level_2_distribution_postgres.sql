-- ============================================
-- TEST 11: SHARE SHIFT CRITIQUE
-- pending: 10% → 40% (+30 points)
-- ============================================

-- 1. NETTOYER
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- 2. PÉRIODE DE RÉFÉRENCE: Distribution normale
-- pending=10%, completed=80%, cancelled=10%
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1,
    CURRENT_DATE - (60 + (i % 30))::integer,
    150 + (i % 100),
    CASE 
        WHEN i <= 100 THEN 'pending'
        WHEN i <= 900 THEN 'completed'
        ELSE 'cancelled'
    END,
    CURRENT_DATE - (60 + (i % 30))::integer
FROM generate_series(1, 1000) as i;

-- 3. PÉRIODE DE COMPARAISON: pending EXPLOSE à 40% 🚨
-- pending=40%, completed=50%, cancelled=10%
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1,
    CURRENT_DATE - (i % 30)::integer,
    150 + (i % 100),
    CASE 
        WHEN i <= 400 THEN 'pending'       -- 🚨 400 au lieu de 100!
        WHEN i <= 900 THEN 'completed'
        ELSE 'cancelled'
    END,
    CURRENT_DATE - (i % 30)::integer
FROM generate_series(1, 1000) as i;

-- 4. VÉRIFICATION
SELECT 
    '📊 REFERENCE' as period, status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / 1000.0, 1) as pct
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '120 days'
  AND order_date < CURRENT_DATE - INTERVAL '30 days'
GROUP BY status

UNION ALL

SELECT 
    '📊 COMPARISON' as period, status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / 1000.0, 1) as pct
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status
ORDER BY period, status;
```

**Résultat attendu:**
```
period       | status    | count | pct
-------------|-----------|-------|-----
REFERENCE    | cancelled |   100 | 10.0
REFERENCE    | completed |   800 | 80.0
REFERENCE    | pending   |   100 | 10.0
COMPARISON   | cancelled |   100 | 10.0
COMPARISON   | completed |   500 | 50.0
COMPARISON   | pending   |   400 | 40.0  🚨

-- ============================================
-- TEST 12: BEHAVIOR ANOMALY CRITIQUE
-- completed: panier moyen +85%
-- ============================================

-- 1. NETTOYER
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- 2. PÉRIODE DE RÉFÉRENCE: Panier moyen = 150€
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1,
    CURRENT_DATE - (60 + (i % 30))::integer,
    150.00 as total_amount,  -- 150€ fixe
    CASE 
        WHEN i <= 100 THEN 'pending'
        WHEN i <= 900 THEN 'completed'
        ELSE 'cancelled'
    END,
    CURRENT_DATE - (60 + (i % 30))::integer
FROM generate_series(1, 1000) as i;

-- 3. PÉRIODE DE COMPARAISON: Panier moyen completed = 277.50€ (+85%) 🚨
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1,
    CURRENT_DATE - (i % 30)::integer,
    CASE 
        WHEN i <= 100 THEN 150.00                    -- pending: stable à 150€
        WHEN i <= 900 THEN 277.50                    -- 🚨 completed: 277.50€ (+85%)
        ELSE 150.00                                   -- cancelled: stable à 150€
    END as total_amount,
    CASE 
        WHEN i <= 100 THEN 'pending'
        WHEN i <= 900 THEN 'completed'
        ELSE 'cancelled'
    END,
    CURRENT_DATE - (i % 30)::integer
FROM generate_series(1, 1000) as i;

-- 4. VÉRIFICATION
SELECT 
    '📊 REFERENCE' as period, status,
    COUNT(*) as count,
    ROUND(AVG(total_amount), 2) as avg_amount
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '120 days'
  AND order_date < CURRENT_DATE - INTERVAL '30 days'
GROUP BY status

UNION ALL

SELECT 
    '📊 COMPARISON' as period, status,
    COUNT(*) as count,
    ROUND(AVG(total_amount), 2) as avg_amount
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status
ORDER BY period, status;
```

**Résultat attendu:**
```
period       | status    | count | avg_amount
-------------|-----------|-------|------------
REFERENCE    | cancelled |   100 |     150.00
REFERENCE    | completed |   800 |     150.00
REFERENCE    | pending   |   100 |     150.00
COMPARISON   | cancelled |   100 |     150.00
COMPARISON   | completed |   800 |     277.50  🚨 (+85%)
COMPARISON   | pending   |   100 |     150.00



-- ============================================
-- TEST 13: NOUVEAU SEGMENT APPARU
-- "refunded" apparaît à 15%
-- ============================================

-- 1. NETTOYER
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- 2. PÉRIODE DE RÉFÉRENCE: Seulement pending/completed/cancelled
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1,
    CURRENT_DATE - (60 + (i % 30))::integer,
    150 + (i % 100),
    CASE 
        WHEN i <= 100 THEN 'pending'
        WHEN i <= 900 THEN 'completed'
        ELSE 'cancelled'
    END,
    CURRENT_DATE - (60 + (i % 30))::integer
FROM generate_series(1, 1000) as i;

-- 3. PÉRIODE DE COMPARAISON: "refunded" apparaît à 15% 🚨
-- pending=10%, completed=65%, cancelled=10%, refunded=15%
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1,
    CURRENT_DATE - (i % 30)::integer,
    150 + (i % 100),
    CASE 
        WHEN i <= 100 THEN 'pending'
        WHEN i <= 750 THEN 'completed'
        WHEN i <= 850 THEN 'cancelled'
        ELSE 'refunded'                    -- 🚨 NOUVEAU SEGMENT!
    END,
    CURRENT_DATE - (i % 30)::integer
FROM generate_series(1, 1000) as i;

-- 4. VÉRIFICATION
SELECT 
    '📊 REFERENCE' as period, status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / 1000.0, 1) as pct
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '120 days'
  AND order_date < CURRENT_DATE - INTERVAL '30 days'
GROUP BY status

UNION ALL

SELECT 
    '📊 COMPARISON' as period, status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / 1000.0, 1) as pct
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status
ORDER BY period, status;
```

**Résultat attendu:**
```
period       | status    | count | pct
-------------|-----------|-------|-----
REFERENCE    | cancelled |   100 | 10.0
REFERENCE    | completed |   800 | 80.0
REFERENCE    | pending   |   100 | 10.0
COMPARISON   | cancelled |   100 | 10.0
COMPARISON   | completed |   650 | 65.0
COMPARISON   | pending   |   100 | 10.0
COMPARISON   | refunded  |   150 | 15.0  🚨 NOUVEAU!
```

**Résultat attendu:**
```
❌ Failed: 1
anomalies_count: 2

Anomalies détectées:
- type: "segment_share_shift"
  segment_value: "refunded"
  reference_share: 0.0
  comparison_share: 15.0
  share_change: +15.0
  severity: "medium"
  
- type: "segment_share_shift"
  segment_value: "completed"
  reference_share: 80.0
  comparison_share: 65.0
  share_change: -15.0
  severity: "medium"


-- ============================================
-- TEST 16: DONNÉES INSUFFISANTES
-- Seulement 8 commandes au total
-- ============================================

-- 1. NETTOYER
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- 2. PÉRIODE DE RÉFÉRENCE: 5 commandes seulement
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at) VALUES
(1, CURRENT_DATE - INTERVAL '60 days', 150.00, 'completed', CURRENT_DATE - INTERVAL '60 days'),
(2, CURRENT_DATE - INTERVAL '55 days', 160.00, 'completed', CURRENT_DATE - INTERVAL '55 days'),
(3, CURRENT_DATE - INTERVAL '50 days', 140.00, 'pending', CURRENT_DATE - INTERVAL '50 days'),
(4, CURRENT_DATE - INTERVAL '45 days', 170.00, 'completed', CURRENT_DATE - INTERVAL '45 days'),
(5, CURRENT_DATE - INTERVAL '40 days', 130.00, 'cancelled', CURRENT_DATE - INTERVAL '40 days');

-- 3. PÉRIODE DE COMPARAISON: 3 commandes seulement
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at) VALUES
(6, CURRENT_DATE - INTERVAL '15 days', 155.00, 'completed', CURRENT_DATE - INTERVAL '15 days'),
(7, CURRENT_DATE - INTERVAL '10 days', 165.00, 'completed', CURRENT_DATE - INTERVAL '10 days'),
(8, CURRENT_DATE - INTERVAL '5 days', 145.00, 'pending', CURRENT_DATE - INTERVAL '5 days');

-- 4. VÉRIFICATION
SELECT COUNT(*) as total FROM demo.orders;
-- Attendu: 8

SELECT 
    CASE 
        WHEN order_date >= CURRENT_DATE - INTERVAL '120 days' 
         AND order_date < CURRENT_DATE - INTERVAL '30 days' 
        THEN 'REFERENCE'
        WHEN order_date >= CURRENT_DATE - INTERVAL '30 days' 
        THEN 'COMPARISON'
    END as period,
    COUNT(*) as count
FROM demo.orders
GROUP BY period;
-- Attendu: REFERENCE=5, COMPARISON=3
```

**Résultat attendu:**
```
✅ Passed: 1
anomalies_count: 0
message: "Insufficient data for distribution analysis"

-- Période de comparaison: BUG! 40% pending 🚨
INSERT INTO demo.orders (customer_id, order_date, total_amount, status)
SELECT 
    (random() * 100 + 1)::int,
    CURRENT_DATE - (random() * 30)::int,
    (random() * 200 + 50)::numeric(10,2),
    CASE 
        WHEN random() < 0.40 THEN 'pending'  -- 🚨 ANOMALIE
        WHEN random() < 0.90 THEN 'completed'
        ELSE 'cancelled'
    END
FROM generate_series(1, 1000);

--- verifcation
-- Vérifier combien de commandes dans chaque période
SELECT 
    CASE 
        WHEN order_date >= CURRENT_DATE - INTERVAL '120 days' 
         AND order_date < CURRENT_DATE - INTERVAL '30 days' 
        THEN 'REFERENCE (J-120 à J-31)'
        
        WHEN order_date >= CURRENT_DATE - INTERVAL '30 days' 
        THEN 'COMPARISON (J-30 à aujourd''hui)'
        
        ELSE 'OUTSIDE PERIODS'
    END as period,
    COUNT(*) as order_count
FROM demo.orders
GROUP BY period
ORDER BY period;


-- ============================================
-- TEST 14: SEGMENT DISPARU
-- "cancelled" disparaît complètement
-- ============================================

-- 1. NETTOYER
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- 2. PÉRIODE DE RÉFÉRENCE: Distribution normale
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1,
    CURRENT_DATE - (60 + (i % 30))::integer,
    150 + (i % 100),
    CASE 
        WHEN i <= 100 THEN 'pending'
        WHEN i <= 900 THEN 'completed'
        ELSE 'cancelled'
    END,
    CURRENT_DATE - (60 + (i % 30))::integer
FROM generate_series(1, 1000) as i;

-- 3. PÉRIODE DE COMPARAISON: "cancelled" disparaît! 🚨
-- pending=11%, completed=89%, cancelled=0%
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at)
SELECT 
    (i % 100) + 1,
    CURRENT_DATE - (i % 30)::integer,
    150 + (i % 100),
    CASE 
        WHEN i <= 110 THEN 'pending'
        ELSE 'completed'                   -- 🚨 Jamais 'cancelled'!
    END,
    CURRENT_DATE - (i % 30)::integer
FROM generate_series(1, 1000) as i;

-- 4. VÉRIFICATION
SELECT 
    '📊 REFERENCE' as period, status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / 1000.0, 1) as pct
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '120 days'
  AND order_date < CURRENT_DATE - INTERVAL '30 days'
GROUP BY status

UNION ALL

SELECT 
    '📊 COMPARISON' as period, status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / 1000.0, 1) as pct
FROM demo.orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status
ORDER BY period, status;
```

**Résultat attendu:**
```
period       | status    | count | pct
-------------|-----------|-------|-----
REFERENCE    | cancelled |   100 | 10.0
REFERENCE    | completed |   800 | 80.0
REFERENCE    | pending   |   100 | 10.0
COMPARISON   | completed |   890 | 89.0
COMPARISON   | pending   |   110 | 11.0
(pas de cancelled!) 🚨
```

**Résultat attendu:**
```
❌ Failed: 1
anomalies_count: 1

Anomalie détectée:
- type: "segment_share_shift"
  segment_value: "cancelled"
  reference_share: 10.0
  comparison_share: 0.0
  share_change: -10.0
  severity: "medium"



-- ============================================
-- TEST 16: DONNÉES INSUFFISANTES
-- Seulement 8 commandes au total
-- ============================================

-- 1. NETTOYER
TRUNCATE TABLE demo.orders RESTART IDENTITY CASCADE;

-- 2. PÉRIODE DE RÉFÉRENCE: 5 commandes seulement
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at) VALUES
(1, CURRENT_DATE - INTERVAL '60 days', 150.00, 'completed', CURRENT_DATE - INTERVAL '60 days'),
(2, CURRENT_DATE - INTERVAL '55 days', 160.00, 'completed', CURRENT_DATE - INTERVAL '55 days'),
(3, CURRENT_DATE - INTERVAL '50 days', 140.00, 'pending', CURRENT_DATE - INTERVAL '50 days'),
(4, CURRENT_DATE - INTERVAL '45 days', 170.00, 'completed', CURRENT_DATE - INTERVAL '45 days'),
(5, CURRENT_DATE - INTERVAL '40 days', 130.00, 'cancelled', CURRENT_DATE - INTERVAL '40 days');

-- 3. PÉRIODE DE COMPARAISON: 3 commandes seulement
INSERT INTO demo.orders (customer_id, order_date, total_amount, status, created_at) VALUES
(6, CURRENT_DATE - INTERVAL '15 days', 155.00, 'completed', CURRENT_DATE - INTERVAL '15 days'),
(7, CURRENT_DATE - INTERVAL '10 days', 165.00, 'completed', CURRENT_DATE - INTERVAL '10 days'),
(8, CURRENT_DATE - INTERVAL '5 days', 145.00, 'pending', CURRENT_DATE - INTERVAL '5 days');

-- 4. VÉRIFICATION
SELECT COUNT(*) as total FROM demo.orders;
-- Attendu: 8

SELECT 
    CASE 
        WHEN order_date >= CURRENT_DATE - INTERVAL '120 days' 
         AND order_date < CURRENT_DATE - INTERVAL '30 days' 
        THEN 'REFERENCE'
        WHEN order_date >= CURRENT_DATE - INTERVAL '30 days' 
        THEN 'COMPARISON'
    END as period,
    COUNT(*) as count
FROM demo.orders
GROUP BY period;
-- Attendu: REFERENCE=5, COMPARISON=3
```

**Résultat attendu:**
```
✅ Passed: 1
anomalies_count: 0
message: "Insufficient data for distribution analysis"