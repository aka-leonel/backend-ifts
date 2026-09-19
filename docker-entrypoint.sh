#!/bin/sh
set -e

# 1. Aplicar las migraciones de Alembic (crea las tablas)
alembic upgrade head

# 2. Poblado de datos iniciales
python seed.py

# 3. Iniciar la API con Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
