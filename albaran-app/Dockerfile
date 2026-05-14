FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Sin buffering en stdout/stderr — logs aparecen inmediatamente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=run.py

EXPOSE 8000

# Arranque inlineado para máxima visibilidad en logs
CMD ["sh", "-c", "\
echo '════ ALBARAN-APP ARRANQUE ════' && \
echo \"Hora: $(date -u)\" && \
echo \"PORT: ${PORT:-8000}\" && \
echo \"DATABASE_URL definida: $([ -n \"$DATABASE_URL\" ] && echo SI || echo NO)\" && \
echo \"FLASK_APP: $FLASK_APP\" && \
echo '──── 1/3 Migraciones ────' && \
flask db upgrade 2>&1 || echo '⚠ flask db upgrade FALLO' && \
echo '──── 2/3 Admin seed ────' && \
flask seed-admin-env 2>&1 || echo '⚠ seed-admin-env FALLO' && \
echo '──── 3/3 Demo seed ────' && \
flask seed-demo 2>&1 || echo '⚠ seed-demo FALLO' && \
echo '──── Arrancando Gunicorn ────' && \
exec gunicorn run:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --access-logfile - --error-logfile -"]
