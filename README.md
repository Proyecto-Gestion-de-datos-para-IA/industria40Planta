# 🏭 Gemelo Digital Industrial 4.0 - Mantenimiento Predictivo con IA

![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)
![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-Event_Streaming-231F20?style=flat-square&logo=apachekafka)
![Apache Spark](https://img.shields.io/badge/Apache_Spark-Data_Processing-E25A1C?style=flat-square&logo=apachespark)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Relational_DB-4169E1?style=flat-square&logo=postgresql)
![MinIO](https://img.shields.io/badge/MinIO-Data_Lake-C7202C?style=flat-square&logo=minio)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit)

## 📖 Descripción del Proyecto

Este proyecto es una plataforma completa de **Ingeniería del Caos y Mantenimiento Predictivo** diseñada para entornos industriales (Industria 4.0). Simula el comportamiento de una planta de 20 máquinas mediante un Gemelo Digital, procesa la telemetría en tiempo real, aplica Inteligencia Artificial (Random Forest) para predecir fallas antes de que ocurran, y almacena los datos en un Data Lake para su posterior reentrenamiento (MLOps).

## 🏗️ Arquitectura del Sistema

El flujo de datos sigue una arquitectura moderna orientada a eventos:

1. **Simulador IoT (Productor):** Genera datos sintéticos de temperatura y vibración en base a estados controlados (Normal, Fricción, Desalineación, etc.).
2. **Apache Kafka (Modo KRaft):** Actúa como el bus de mensajes de alta velocidad (`telemetria_sensores`).
3. **Apache Spark (Streaming):** Procesa los datos en ventanas de 60 segundos, consulta el modelo de Machine Learning (`.pkl`) y emite un veredicto.
4. **PostgreSQL (Hot Storage):** Almacena las predicciones recientes y el estado maestro de las máquinas.
5. **MinIO (Cold Storage / Data Lake):** Guarda el histórico inmutable en formato `.parquet` para análisis forense y reentrenamiento.
6. **FastAPI & Streamlit:** Exponen los datos a través de una API REST y un Dashboard interactivo en tiempo real.

---

## 🚀 Requisitos Previos

Para desplegar esta arquitectura, ya sea en un entorno local o en un servidor VPS, solo necesitas:

- [Docker Engine](https://docs.docker.com/engine/install/) (v20.0+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)
- Al menos **4GB de RAM** disponible (8GB recomendados para Spark/Kafka).

---

## ⚙️ Instalación y Despliegue

### 1. Clonar el repositorio

```bash
git clone [https://github.com/](https://github.com/)<TU_USUARIO>/<TU_REPO>.git
cd <TU_REPO>
```
