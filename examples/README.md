# 2QC+ Examples

Exemples pratiques pour démarrer avec 2QC+ Data Quality Framework.

## 🚀 Quick Start

python3.11 -m pip install -e .
qc2plus --help

### 1. Démarrer la base de données

```bash
# Depuis la racine du projet
docker-compose up -d postgres

# check containers
docker-compose ps

# check container log
docker-compose logs --tail=200 postgres

# log to database
docker exec -it qc2plus-postgres psql -U qc2plus -d qc2plus_demo
```

```bash
# Depuis la racine du projet
docker-compose build qc2plus-runner

docker-compose up -d qc2plus-runner

# check containers
docker-compose ps

# check container log
docker-compose logs --tail=200 qc2plus-runner

docker exec -it qc2plus-runner /bin/bash

cd examples/basic

qc2plus --help
qc2plus test-connection --target demo 
qc2plus run --target demo --level 1


cd examples/advanced

qc2plus --help
qc2plus test-connection --target demo 
qc2plus run --target demo --level all
qc2plus run --target demo --level 1 --models customer_datamart

```

```sh
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd

sql = """
        -- Test: Email format validation on email
        SELECT 
            'email' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM basic_demo.customers) as total_rows,
            'Invalid email format found in email' as message
        FROM basic_demo.customers
        WHERE email IS NOT NULL
        AND NOT (
            email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        )
        GROUP BY 1,4
        HAVING COUNT(*) > 0
"""

sql_2 = """
        -- Test: Email format validation on email
        SELECT 
            'email' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM basic_demo.customers) as total_rows,
            'Invalid email format found in email' as message
        FROM basic_demo.customers
        WHERE email IS NOT NULL
        AND NOT (
            email = 'toto'
        )
        GROUP BY 1,4
        HAVING COUNT(*) > 0
"""

user = "qc2plus"
password = "qc2plus_password"
host = "postgres"
port = 5432
dbname = "qc2plus_demo"

def _create_postgresql_engine() -> Engine:
    """Create PostgreSQL engine"""
    connection_string = (
        f"postgresql://{user}:{password}"
        f"@{host}:{port}"
        f"/{dbname}"
    )
    return create_engine(connection_string)

engine = _create_postgresql_engine()

def connection_manager_execute_query(query):
  with engine.connect() as conn:
      return pd.read_sql(text(query), conn)

df = connection_manager_execute_query(sql)
```

### 2. Lancer l'exemple basique
```bash
# Depuis la racine du projet
docker-compose build qc2plus-basic

docker-compose up -d qc2plus-basic

# check containers
docker-compose ps

# check container log
docker-compose logs --tail=200 qc2plus-basic

docker exec -it qc2plus-basic /bin/bash

cd examples/basic
qc2plus --help
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
