#!/bin/sh
# Script de arranque robusto para Railway.
# Cada paso imprime su estado y la app arranca aunque los seeds fallen.

set -u  # error si una variable no existe (pero NO en errores de comandos)

echo "════════════════════════════════════════════════════"
echo "  Albaran-app — arranque"
echo "  Fecha: $(date -u)"
echo "  PORT:  ${PORT:-8000}"
echo "════════════════════════════════════════════════════"

echo ""
echo "[1/4] Aplicando migraciones de base de datos..."
flask db upgrade || echo "⚠ flask db upgrade falló — continuando..."

echo ""
echo "[2/4] Verificando admin (SEED_ADMIN)..."
flask seed-admin-env || echo "⚠ flask seed-admin-env falló — continuando..."

echo ""
echo "[3/4] Verificando datos demo (SEED_DEMO)..."
flask seed-demo || echo "⚠ flask seed-demo falló — continuando..."

echo ""
echo "[4/4] Arrancando gunicorn en 0.0.0.0:${PORT:-8000}..."
echo "════════════════════════════════════════════════════"
exec gunicorn run:app \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
