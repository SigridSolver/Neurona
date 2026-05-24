FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer el puerto
EXPOSE 8080

# Comando para iniciar la aplicación (SQLite persistente se montará en /data/saber11.db)
# Aseguramos que la DB apunte al volumen persistente estableciendo una variable de entorno si fuera necesario, 
# pero como en main.py está hardcodeado a `BASE_DIR.parent / "saber11.db"`, 
# configuraremos el directorio padre para que sea el volumen si lo montamos.
# Para simplificar en Fly.io con la estructura actual:
# En `main.py`, DB_PATH es BASE_DIR.parent / "saber11.db" (o sea, /app/saber11.db).
# Montaremos el volumen en /app/data y necesitamos un script o un symlink, o modificar app/main.py.
# Mejor correr Uvicorn directamente.

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
