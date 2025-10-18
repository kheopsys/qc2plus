-- ============================================
-- 🧩 TEST 3 : Corrélation anormalement forte non attendue
-- ============================================
-- Objectif :
--   Vérifier que le framework (CorrelationAnalyzer) détecte une corrélation
--   très forte alors qu’aucune corrélation n’était attendue.
--
-- Rappel du principe :
--   expected_correlation = 0.0   → on ne s’attend à aucun lien linéaire
--   threshold n’est pas utilisé ici
--
--   Dans le code, le test déclenche une anomalie si :
--     expected_correlation est None ou 0
--     ET |corrélation_mesurée| > 0.7
--
-- Exemple attendu de message :
--   "Unexpectedly strong correlation 0.9998"
--
-- ============================================
-- 1️⃣ Création de la table de test
-- ============================================
CREATE TABLE demo.correlation_test_3 (
    user_id INT,
    impressions INT,
    clicks INT
);

-- ============================================
-- 2️⃣ Insertion des données
-- Données volontairement très corrélées :
--   Les clics augmentent presque parfaitement avec les impressions.
--   Pourtant, le test suppose qu’il ne devrait pas y avoir de corrélation.
-- ============================================
INSERT INTO demo.correlation_test_3 (user_id, impressions, clicks) VALUES
(1, 100, 10),
(2, 200, 20),
(3, 300, 29),
(4, 400, 40),
(5, 500, 51),
(6, 600, 60),
(7, 700, 70),
(8, 800, 80),
(9, 900, 89),
(10, 1000, 100);

-- Corrélation approximative : r ≈ 0.9998
-- expected_correlation = 0.0
-- => |0.9998| > 0.7 → Déclenche l’erreur :
--    "Unexpectedly strong correlation 0.980"
--
-- ============================================
-- ✅ Résultat attendu du framework QC2+
-- ============================================
--   {
--     "passed": false,
--     "anomalies_count": 1,
--     "message": "Static correlation anomalies: 1",
--     "details": {
--       "static_correlation": {
--         "anomalies": [
--           {
--             "variable_pair": "impressions_vs_clicks",
--             "correlation": 0.98,
--             "expected_correlation": null,
--             "reason": "Unexpectedly strong correlation 0.980",
--             "severity": "low"
--           }
--         ]
--       }
--     }
--   }
--
