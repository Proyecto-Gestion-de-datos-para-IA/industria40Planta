#!/bin/bash

echo -e "\e[34m[INFO]\e[0m Iniciando secuencia de despliegue - Industria 4.0"

# 1. Cimientos
echo -e "\e[34m[INFO]\e[0m Levantando Postgres y MinIO..."
docker compose up -d iot-postgres minio nginx-proxy
sleep 10 

# 2. Cola de Mensajería
echo -e "\e[34m[INFO]\e[0m Levantando Kafka (KRaft)..."
docker compose up -d kafka
sleep 15 

# 3. Creador del tópico
echo -e "\e[34m[INFO]\e[0m Levantando Simulador IoT..."
docker compose up -d simulador-iot
sleep 5

# 4. Procesamiento
echo -e "\e[34m[INFO]\e[0m Levantando Motor de Decisiones Spark..."
docker compose up -d iot-spark-app
sleep 10

# 5. Frontend
echo -e "\e[34m[INFO]\e[0m Levantando API y Dashboard..."
docker compose up -d api-servicio dashboard

echo -e "\e[32m[OK]\e[0m ¡Infraestructura Desplegada Exitosamente!"
docker compose ps