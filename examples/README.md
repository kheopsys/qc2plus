# 2QC+ Examples

Exemples pratiques pour démarrer avec 2QC+ Data Quality Framework.

## 🚀 Quick Start

### 1. Démarrer la base de données
```bash
# Depuis la racine du projet
docker-compose up -d postgres
```

### 2. Lancer l'exemple basique
```bash
cd examples/basic
qc2plus test-connection --target demo
qc2plus run --target demo
```

### 3. Lancer l'exemple avancé
```bash
cd examples/advanced  
qc2plus test-connection --target demo
qc2plus run --target demo --level all
```

## 📁 Structure

```
examples/
├── basic/              # Tests Level 1 seulement
│   ├── qc2plus_project.yml
│   ├── profiles.yml
│   └── models/customers.yml
└── advanced/           # Tests Level 1 + Level 2 (ML)
    ├── qc2plus_project.yml
    ├── profiles.yml
    └── models/customers.yml
```

## 🔍 Différences entre Basic et Advanced

| Aspect | Basic | Advanced |
|--------|-------|----------|
| **Tests** | Level 1 seulement | Level 1 + Level 2 (ML) |
| **Alertes** | Aucune | Slack |
| **Schema DB** | `basic_demo` | `advanced_demo` |
| **Durée** | ~10 secondes | ~30 secondes |

## 📊 Tests Inclus

### Basic Example
- ✅ `unique` - Unicité customer_id
- ✅ `not_null` - Email obligatoire  
- ✅ `email_format` - Format email valide
- ✅ `range_check` - Âge entre 0-120

### Advanced Example  
- ✅ **Level 1** : Tous les tests Basic
- ✅ **Correlation** : Analyse lifetime_value vs order_frequency
- ✅ **Temporal** : Patterns temporels sur created_at
- ✅ **Multivariate** : Détection outliers ML (Isolation Forest, LOF)

## 🐳 Avec Docker

### Démarrage complet
```bash
# Tout démarrer d'un coup
docker-compose up -d

# Voir les logs des exemples
docker-compose logs qc2plus-basic
docker-compose logs qc2plus-advanced
```

### Commandes utiles
```bash
# Accéder à un container
docker-compose exec qc2plus-basic bash

# Voir la base de données
docker-compose exec postgres psql -U qc2plus -d qc2plus_demo

# Redémarrer un exemple
docker-compose restart qc2plus-advanced
```

## 📈 Résultats

### Voir les résultats dans la DB
```sql
-- Résumé des exécutions
SELECT * FROM quality_run_summary ORDER BY execution_time DESC LIMIT 5;

-- Détail des tests
SELECT model_name, test_name, status, message 
FROM quality_test_results 
WHERE execution_time >= CURRENT_DATE;

-- Anomalies ML (Advanced seulement)
SELECT * FROM quality_anomalies ORDER BY detection_time DESC LIMIT 10;
```

### Logs des tests
```bash
# Basic
tail -f examples/basic/logs/qc2plus.log

# Advanced  
tail -f examples/advanced/logs/qc2plus.log
```

## ⚙️ Configuration

### Variables d'environnement
```bash
# Pour les alertes Slack (Advanced)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/your/webhook"
```

### Modifier les tests
Éditez `models/customers.yml` dans chaque exemple :

```yaml
# Ajouter un nouveau test Level 1
- accepted_values:
    column_name: status
    accepted_values: ['active', 'inactive']
    severity: medium

# Ajouter une analyse Level 2 (Advanced seulement)
distribution_analysis:
  segments: [country, customer_segment]
  metrics: [lifetime_value]
```

## 🚨 Troubleshooting

### La base n'est pas prête
```bash
# Vérifier le statut
docker-compose ps postgres

# Voir les logs
docker-compose logs postgres
```

### Tests échouent
```bash
# Mode debug
QC2PLUS_LOG_LEVEL=DEBUG qc2plus run --target demo

# Vérifier la connexion
qc2plus test-connection --target demo
```

### Données manquantes
```bash
# Réinitialiser la base
docker-compose down -v
docker-compose up -d postgres
# Attendre 30 secondes pour l'initialisation
```

## 🎯 Prochaines Étapes

1. **Personnaliser** : Modifier les tests dans `models/customers.yml`
2. **Ajouter des modèles** : Créer `models/orders.yml`, etc.
3. **Configurer alertes** : Ajouter Email, Teams
4. **Planifier** : Utiliser cron pour exécutions automatiques

## 📚 Références

- [Documentation 2QC+](../README.md)
- [Configuration des tests](../docs/tests.md)
- [Guide alerting](../docs/alerting.md)
