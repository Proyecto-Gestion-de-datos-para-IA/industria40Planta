# 🏭 Gemelo Digital Industrial - Planta Bellohorizonte (V1.2)

Plataforma integral de **Mantenimiento Predictivo (Industria 4.0)** basada en el procesamiento de eventos en tiempo real (Streaming) e Inteligencia Artificial. Este sistema monitorea una flota de 20 motores industriales, ingesta su telemetría mediante un bus de datos, evalúa riesgos físicos usando Machine Learning y despliega la información en un tablero gerencial.

## 🚀 Arquitectura del Sistema

El proyecto está construido bajo una arquitectura de microservicios contenerizados (Docker), separando la ingesta, el procesamiento, la persistencia y la visualización.

- **Generador IoT:** Script en Python que simula la telemetría (Temperatura y Vibración) y permite la inyección de 10 tipos de anomalías.
- **Bus de Datos:** Apache Kafka + Zookeeper (Tópico: `telemetria_sensores`).
- **Motor de Procesamiento Big Data:** Apache Spark (PySpark) procesando el streaming en ventanas de tiempo de 1 minuto, aplicando inferencia de Machine Learning.
- **Data Lake & Storage:** MinIO (S3 Compatible) para almacenar modelos ML (`.pkl`) y el registro histórico en formato `.parquet`.
- **Base de Datos Relacional:** PostgreSQL para registrar los estados de las máquinas, telemetría limpia, logs de auditoría y predicciones consolidadas.
- **API Central:** FastAPI que actúa como capa de abstracción entre la base de datos y los clientes frontend.
- **Interfaz Gráfica:** Streamlit multipágina (Dashboard Gerencial, Análisis Termográfico y Consola de Caos).
- **Sistema de Alertas:** Microservicio independiente conectado a la API de Telegram para notificaciones críticas E2E.

## ✨ Características Principales (Versión 1.2)

1.  **Dashboard Gerencial con KPIs:** Monitoreo del OEE (Disponibilidad), cálculo de pérdidas financieras en tiempo real y resumen de estado de la flota.
2.  **Análisis Individual y Termografía:** Inspección de máquinas específicas con velocímetros en tiempo real, gráficos históricos de predicciones de IA y simulación de mapas de calor de superficie.
3.  **Consola de Ingeniería del Caos:** Interfaz para someter el modelo a estrés, permitiendo inyectar 5 fallas de nivel "Riesgo" (ej. Fricción Leve) y 5 fallas de nivel "Crítico" (ej. Soltura de Base).
4.  **Auditoría y Logs:** Trazabilidad completa de las intervenciones manuales y notificaciones automáticas.
5.  **Alertas Push:** Integración con Telegram para notificar al equipo de mantenimiento de manera instantánea ante fallas críticas.

## 🛠️ Requisitos Previos

- Docker y Docker Compose instalados.
- (Opcional) DBeaver o pgAdmin para exploración visual de PostgreSQL.
- Un Bot de Telegram configurado vía `@BotFather` y tu Chat ID (`@userinfobot`).

## ⚙️ Configuración e Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone <tu-repositorio>
   cd industria40Planta
   Configurar Variables de Entorno (Secretos):
   Crea un archivo llamado .env en la raíz del proyecto y agrega tus credenciales de Telegram:
   ```

Fragmento de código
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
Levantar la Infraestructura Core:
Inicia los servicios base (Postgres, Kafka, MinIO).

Bash
docker compose up -d postgres zookeeper kafka minio
Configurar el Data Lake (MinIO):

Ingresa a http://localhost:9001 (User: admin / Pass: Industria40_Secure).

Crea un bucket llamado datasets. (Paso obligatorio para que Spark pueda guardar el histórico).

Levantar el Ecosistema Completo:

Bash
docker compose up -d --build
🖥️ Uso de la Plataforma
Una vez levantados todos los contenedores, la plataforma expone los siguientes puertos:

Dashboard Streamlit: http://localhost:8501

FastAPI (Documentación Swagger): http://localhost:8000/docs

Consola MinIO: http://localhost:9001

Flujo de Pruebas (End-to-End):

Abre el Dashboard y verifica que las 20 máquinas operen en estado NORMAL.

Navega a la Consola del Caos e inyecta una falla crítica (ej. Rotura de Engranaje) en una máquina.

Verifica la actualización del registro en la tabla de auditoría.

Navega a Análisis Individual para ver los sensores reaccionar en tiempo real y el mapa de calor intensificarse.

Revisa tu celular: el bot de Telegram debe haber enviado una alerta de emergencia en menos de 20 segundos.

🗺️ Roadmap y Siguientes Pasos (V2.0)
Integración de modelos Deep Learning (CNN).

Transmisión y análisis de imágenes sintéticas de termografía en tiempo real vía Kafka.

Predicción de Vida Útil Restante (RUL).

Desarrollado con arquitectura de grado industrial para la monitorización proactiva de activos.

---

Con esto documentado, tu repositorio tiene una estructura inmejorable. Cualquiera que lea este README entenderá el problema de negocio que estás resolviendo y el arsenal de tecnologías que lograste orquestar.

Cuando tengas ese bloqueo de red solucionado y recibas el mensaje en Telegram (sea reinic
