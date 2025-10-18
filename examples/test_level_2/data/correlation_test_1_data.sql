-- ============================================
-- 🧩 TEST 1 : Corrélation dégradée par rapport à l’attendu
-- ============================================
-- Objectif :
--   Vérifier que le framework (CorrelationAnalyzer) détecte une corrélation
--   plus faible que la corrélation attendue.
--
-- Rappel du principe :
--   expected_correlation = 0.9  → on s’attend à une corrélation très forte
--   threshold = 0.2            → on accepte un écart max de 0.2
--
--   Donc si la corrélation réelle < (0.9 - 0.2) = 0.7
--   → le framework doit lever une erreur de type :
--     "Correlation X deviates from expected Y by Z"
--
-- Conséquence :
--   Le coefficient de corrélation mesuré (r) ≈ 0.5
--   L’écart avec la corrélation attendue (0.9) est de 0.4 > threshold (0.2)
--   --> Le test "correlation_analysis" échoue avec un message du type :
--      "Correlation 0.500 deviates from expected 0.900 by 0.400"
--
--   → Anomalie détectée : corrélation dégradée par rapport à l’attendu


-- ============================================
-- 1️⃣ Création de la table de test
-- ============================================
CREATE TABLE demo.correlation_test_1 (
    user_id INT,
    impressions INT,
    clicks INT
);

-- ============================================
-- 2️⃣ Insertion des données
-- On crée volontairement une corrélation affaiblie :
-- impressions augmente, mais clicks n'augmente pas proportionnellement
-- ============================================
INSERT INTO demo.correlation_test_1 (user_id, impressions, clicks) VALUES
(1, 100, 90),
(2, 200, 150),
(3, 300, 140),
(4, 400, 160),
(5, 500, 200),
(6, 600, 220),
(7, 700, 260),
(8, 800, 250),
(9, 900, 270),
(10, 1000, 280);
