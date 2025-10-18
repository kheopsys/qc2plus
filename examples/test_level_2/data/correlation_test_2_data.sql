-- ============================================
-- 🧩 TEST 2 : Corrélation anormalement faible
-- ============================================
-- Objectif :
--   Vérifier que le framework (CorrelationAnalyzer) détecte un cas
--   où la corrélation observée est beaucoup plus faible que ce qui est attendu.
--
-- Rappel du principe :
--   expected_correlation = 0.8  → on s’attend à une corrélation forte
--   threshold = 0.2             → tolérance max d’écart
--
--   De plus, le framework applique un test spécifique :
--     si |expected_correlation| > 0.5 ET |corrélation_mesurée| < 0.3
--     → il déclenche une anomalie "Unexpectedly weak correlation"
--
-- Conséquence :
--   Même si la déviation absolue est parfois < threshold,
--   ce test est conçu pour détecter des corrélations anormalement faibles
--   dans des cas où la corrélation attendue est censée être forte.
--
-- Exemple attendu de message :
--   "Unexpectedly weak correlation 0.250 (expected 0.800)"
--
-- ============================================
-- 1️⃣ Création de la table de test
-- ============================================
CREATE TABLE demo.correlation_test_2 (
    user_id INT,
    impressions INT,
    clicks INT
);

-- ============================================
-- 2️⃣ Insertion des données
-- Données volontairement peu corrélées :
--   - Les impressions augmentent, mais les clics varient aléatoirement.
--   - Cela crée une corrélation faible malgré une attente forte.
-- ============================================
INSERT INTO demo.correlation_test_2 (user_id, impressions, clicks) VALUES
(1, 100, 300),
(2, 200, 100),
(3, 300, 500),
(4, 400, 200),
(5, 500, 600),
(6, 600, 150),
(7, 700, 550),
(8, 800, 250),
(9, 900, 400),
(10, 1000, 300);

-- Corrélation approximative (r ≈ 0.25)
-- → Inférieure à 0.3, donc "Unexpectedly weak correlation"
--
-- Résultat attendu :
--   {
--     "passed": false,
--     "anomalies_count": 1,
--     "message": "Static correlation anomalies: 1",
--     "details": {
--       "static_correlation": {
--         "anomalies": [
--           {
--             "variable_pair": "impressions_vs_clicks",
--             "correlation": 0.25,
--             "expected_correlation": 0.80,
--             "reason": "Unexpectedly weak correlation 0.250 (expected 0.800)",
--             "severity": "low"
--           }
--         ]
--       }
--     }
--   }
--
-- ============================================
-- 🔧 Module YAML associé
-- ============================================
models:
  - name: correlation_test_2
    description: "Test de corrélation anormalement faible entre impressions et clicks"

    qc2plus_tests:
      level1:
        - unique:
            column_name: user_id
            severity: critical

      level2:
        - correlation_analysis:
            variables: ["impressions", "clicks"]
            expected_correlation: 0.8     # Corrélation attendue forte
            threshold: 0.2                # Tolérance max d’écart
            correlation_type: "pearson"
            severity: low
