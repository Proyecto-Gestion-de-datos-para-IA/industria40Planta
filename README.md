🏭 Gemelo Digital Industrial 4.0 - Mantenimiento Predictivo con IA
📖 Descripción del Proyecto
Este proyecto es una plataforma completa de Ingeniería del Caos y Mantenimiento Predictivo diseñada para entornos industriales (Industria 4.0). Simula el comportamiento de una planta de 20 máquinas mediante un Gemelo Digital, procesa la telemetría en tiempo real, aplica Inteligencia Artificial (Random Forest) para predecir fallas antes de que ocurran, y almacena los datos en un Data Lake para su posterior reentrenamiento (MLOps).

🏗️ Arquitectura del Sistema
El flujo de datos sigue una arquitectura moderna orientada a eventos:

Simulador IoT (Productor): Genera datos sintéticos de temperatura y vibración en base a estados controlados (Normal, Fricción, Desalineación, Apagada).

Apache Kafka (Modo KRaft): Actúa como el bus de mensajes de alta velocidad (telemetria_sensores).

Apache Spark (Streaming): Procesa los datos en ventanas de 60 segundos, consulta el modelo de Machine Learning (.pkl) y emite un veredicto.

PostgreSQL (Hot Storage): Almacena las predicciones recientes y el estado maestro de las máquinas para lectura ultra rápida.

MinIO (Cold Storage / Data Lake): Guarda el histórico inmutable en formato .parquet para análisis forense y reentrenamiento.

FastAPI & Streamlit: Exponen los datos a través de una API REST y un Dashboard interactivo en tiempo real.

🚀 Requisitos Previos
Para desplegar esta arquitectura, ya sea en un entorno local o en un servidor VPS, solo necesitas:

Docker Engine (v20.0+)

Docker Compose (v2.0+)

Al menos 4GB de RAM disponible (8GB recomendados para evitar saturación de Spark/Kafka).

⚙️ Instalación y Despliegue

1. Clonar el repositorio
   Bash
   git clone https://github.com/<TU_USUARIO>/<TU_REPO>.git
   cd <TU_REPO>
2. Configurar Credenciales (Seguridad)
   Antes de levantar los servicios, asegúrate de configurar las variables de entorno o modificar el archivo docker-compose.yml para establecer tus contraseñas seguras en los siguientes servicios:

PostgreSQL: POSTGRES_PASSWORD=<TU_PASSWORD_DB>

MinIO: MINIO_ROOT_PASSWORD=<TU_PASSWORD_MINIO>

Nota: Asegúrate de actualizar estas mismas credenciales en los archivos de conexión de la API, Spark y los scripts de MLOps.

3. Generar el Modelo Base (Local)
   Antes de desplegar en producción, Spark necesita un modelo de IA inicial para arrancar.

Bash
cd procesamiento_spark
python train_model.py
cd ..
(Esto generará el archivo modelo_falla.pkl localmente. Asegúrate de incluirlo al subir tu código al VPS).

4. Iniciar la Infraestructura (Coreografía)
   Debido a que Kafka y Postgres necesitan tiempo para inicializarse antes de que Spark intente conectarse, utiliza el script de arranque orquestado incluido en la raíz del proyecto:

Bash
chmod +x up.sh
./up.sh
🌐 Accesos a la Plataforma
Una vez que el script up.sh finalice con éxito, los servicios estarán disponibles en los siguientes puertos (si estás en un VPS, reemplaza localhost por la IP pública de tu servidor, o usa tus subdominios si configuraste Nginx Proxy Manager):

Dashboard Operativo: http://localhost:8501

API REST (Documentación): http://localhost:8000/docs

MinIO Console (Data Lake): http://localhost:9001

Nginx Proxy Manager: http://localhost:81

🔄 Ciclo de Vida MLOps (Reentrenamiento)
Este proyecto incluye un pipeline automatizado para reentrenar la IA utilizando los datos reales y dinámicos almacenados en el Data Lake (MinIO).

Cuando el sistema haya recopilado suficiente información de eventos de falla:

Bash
cd mlops_pipeline
pip install -r requirements.txt
python retrain_minio.py
El script leerá los archivos .parquet directamente de MinIO (evitando sobrecargar la base de datos de producción), limpiará los datos de las máquinas apagadas, entrenará un modelo_v2 y lo respaldará automáticamente de forma versionada en el bucket modelos.

📁 Estructura del Proyecto
Plaintext
├── api_servicio/ # Backend FastAPI (Lectura de BD)
├── dashboard/ # Interfaz UI en Streamlit + Consola del Caos
├── mlops_pipeline/ # Scripts de extracción y reentrenamiento ML
├── procesamiento_spark/ # Motor de Streaming, Ventanas de tiempo e Inferencia
├── simulador_iot/ # Productor Kafka y reglas matemáticas de fallas
├── docker-compose.yml # Orquestación global de contenedores
├── init.sql # Esquema de tablas y sembrado inicial de Postgres
└── up.sh # Script de arranque escalonado
👨‍💻 Autor
Desarrollado como proyecto de título / prueba de concepto para la integración avanzada de Tecnologías de la Información, Industria 4.0 y Big Data.
