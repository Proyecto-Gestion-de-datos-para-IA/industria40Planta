# Usamos la imagen oficial de Apache Spark con Python ya configurado
FROM apache/spark-py:latest

USER root

# Instalamos las herramientas necesarias para manejar paquetes de Python
RUN apt-get update && apt-get install -y python3-pip

# Copiamos el archivo de dependencias
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiamos el código y el modelo que ya generaste
COPY spark_streaming.py .
COPY modelo_falla.pkl .

# El comando de ejecución (Spark-submit)
# Nota: Los paquetes de Kafka y Postgres se descargan al arrancar
CMD ["/opt/spark/bin/spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0", \
     "spark_streaming.py"]