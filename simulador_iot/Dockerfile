FROM python:3.11-slim

WORKDIR /app

# Copiamos e instalamos dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código
COPY . .

CMD ["python", "-u","sensor_producer.py"]
CMD ["python", "-u","camara_producer.py"]