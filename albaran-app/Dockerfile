FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Variable de entorno para Flask
ENV FLASK_APP=run.py

# Puerto que expone la app
EXPOSE 8000

# Comando de arranque
CMD ["sh", "-c", "flask db upgrade && flask seed-admin-env && flask seed-demo ; gunicorn run:app --bind 0.0.0.0:8000 --workers 2 --timeout 120"]
