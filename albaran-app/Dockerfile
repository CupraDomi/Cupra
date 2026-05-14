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

# Sin buffering en stdout/stderr — los logs aparecen inmediatamente
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

EXPOSE 8000

# Script de arranque externo para mayor robustez y mejor logging
RUN chmod +x /app/start.sh 2>/dev/null || true

CMD ["sh", "/app/start.sh"]
