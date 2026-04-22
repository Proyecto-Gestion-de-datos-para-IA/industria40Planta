FROM python:3.11-slim

WORKDIR /app

# Copiamos e instalamos dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código y el script de arranque
COPY . .

# Damos permisos de ejecución al script
RUN chmod +x start.sh

# Ejecutamos el script
CMD ["./start.sh"]