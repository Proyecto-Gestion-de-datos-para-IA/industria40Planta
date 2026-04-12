FROM python:3.11-slim
WORKDIR /app
RUN pip install confluent-kafka pandas
COPY sensor_producer.py .
CMD ["python", "-u", "sensor_producer.py"] 
# El -u es para que los print() se vean en tiempo real en los logs de Docker