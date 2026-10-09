#!/bin/bash
set -e

echo "Starting Superset initialization..."

# Mettre à jour la base de données locale Superset (SQLite par défaut pour la metadata)
superset db upgrade

# Créer un utilisateur Admin (ça crashera silencieusement si l'admin existe déjà grâce au || true)
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname Superset \
    --email admin@superset.com \
    --password $SUPERSET_ADMIN_PASSWORD || echo "Admin already exists"

# Initialiser les rôles et permissions
superset init

# Importer la connexion PostgreSQL via Config as Code
superset import_datasources -p /app/superset_config/datasources.yaml || echo "Datasources imported or failed to import"

echo "Initialization complete. Starting Superset web server..."

# Démarrer Gunicorn (standard pour Superset)
exec gunicorn --bind 0.0.0.0:8088 \
    --workers 1 \
    --timeout 120 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    "superset.app:create_app()"
