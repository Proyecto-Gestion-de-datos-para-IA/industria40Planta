FROM python:3.11-slim-bullseye

# Instalamos Java 11 (El estándar de la industria para Spark y PyArrow)
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless procps && \
    apt-get clean

WORKDIR /app

# Instalamos las librerías exactas
RUN pip install pyspark==3.5.0 pandas pyarrow scikit-learn==1.6.1 joblib

COPY . .

CMD ["python", "-u", "spark_streaming.py"]