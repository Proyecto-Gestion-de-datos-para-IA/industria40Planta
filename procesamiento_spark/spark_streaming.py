import os
import joblib
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType, IntegerType
from pyspark.sql.functions import from_json, col, window, avg, when, split, concat_ws, udf, year, month, dayofmonth

#"""
#=============================================================================
#MÓDULO: Motor de Procesamiento y Streaming IA (El "Cerebro" de Spark)
#VERSIÓN: 2.5
#DESCRIPCIÓN: 
#Aplicación PySpark en Streaming continuo. Actúa como el puente principal 
#de la arquitectura Lambda/Kappa de la Planta 4.0. Consume datos de Kafka, 
#aplica inferencia de Machine Learning en vivo, y distribuye los resultados.

#CONTEXTO DE INTELIGENCIA ARTIFICIAL Y DATA LAKE:
#1. Inferencia en vivo: Utiliza un modelo preentrenado (joblib) embebido 
#   como UDF para clasificar el estado de salud de la máquina por ventanas de tiempo.
#2. Capa Speed (Postgres): Envía datos en crudo y predicciones al instante 
#   para alimentar el Dashboard de Streamlit en tiempo real.
#3. Capa Batch/Lake (MinIO): Almacena las ventanas históricas en formato Parquet. 
#   Estos archivos formarán el Dataset histórico masivo (Big Data) para 
#   entrenar los futuros modelos de RUL (Remaining Useful Life) y Series de Tiempo.
#=============================================================================
#"""

# =============================================================================
# 0. CONFIGURACIÓN DEL ENTORNO Y DEPENDENCIAS
# =============================================================================
# Descarga automática de drivers en tiempo de ejecución:
# - spark-sql-kafka: Para leer del bus de mensajería
# - postgresql: Para inyectar datos al dashboard web
# - hadoop-aws / aws-java-sdk: Para simular conexión S3 hacia nuestro MinIO (Data Lake)
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 pyspark-shell'

spark = SparkSession.builder.appName("Industria40_Full_Engine").getOrCreate()

# Configuración de credenciales y rutas para el Data Lake S3-Compatible (MinIO)
sc = spark.sparkContext
sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://minio:9000")
sc._jsc.hadoopConfiguration().set("fs.s3a.access.key", "admin")
sc._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "Industria40_Secure")
sc._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
sc._jsc.hadoopConfiguration().set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

# =============================================================================
# 1. CARGA DEL MODELO DE INTELIGENCIA ARTIFICIAL
# =============================================================================
# Cargamos el modelo pre-entrenado (Clasificación/Anomalías)
modelo = joblib.load('modelo_falla.pkl')

# UDF (User Defined Function): Transforma el modelo de Python estándar a una 
# función distribuida de Spark, capaz de predecir miles de registros por segundo
semaforo_udf = udf(lambda t, v: int(modelo.predict([[t, v]])[0]), IntegerType())

# Estructura estricta para leer el JSON proveniente de Kafka
schema = StructType().add("id_sensor", StringType()).add("valor", DoubleType()).add("timestamp", StringType())


# =============================================================================
# 2. INGESTA: LECTURA CONTINUA DESDE KAFKA
# =============================================================================
raw_stream = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "kafka:9092").option("subscribe", "telemetria_sensores").load()

# Transformación de Binario/String a Columnas Estructuradas SQL
parsed_stream = raw_stream.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*") \
    .withColumn("timestamp", col("timestamp").cast(TimestampType()))


# =============================================================================
# 3. CAPA SPEED (VISUALIZACIÓN EN VIVO - DATOS CRUDOS)
# =============================================================================
# Función ForEachBatch: Inyecta micro-lotes directamente a la BD relacional
def write_raw(batch_df, batch_id):
    db_args = {"user": "admin", "password": "admin123", "driver": "org.postgresql.Driver"}
    batch_df.select(col("id_sensor"), col("valor"), col("timestamp").alias("timestamp_evento")) \
        .write.jdbc("jdbc:postgresql://iot-postgres:5432/industria40", "telemetria_limpia", "append", db_args)

raw_query = parsed_stream.writeStream.foreachBatch(write_raw).start()


# =============================================================================
# 4. CAPA ANALÍTICA E IA (VENTANAS DE TIEMPO)
# =============================================================================
# Agrupación temporal: El modelo ML necesita características agregadas (Promedios), no datos crudos aislados.
windowed_df = parsed_stream.withWatermark("timestamp", "10 seconds") \
    .withColumn("maquina", concat_ws("-", split(col("id_sensor"), "-").getItem(2), split(col("id_sensor"), "-").getItem(3))) \
    .groupBy(window(col("timestamp"), "1 minute"), col("maquina")) \
    .agg(avg(when(col("id_sensor").contains("TEMP"), col("valor"))).alias("t_avg"),
         avg(when(col("id_sensor").contains("VIB"), col("valor"))).alias("v_avg")) \
    .withColumn("decision_id", semaforo_udf(col("t_avg"), col("v_avg"))) # <--- Ejecución del modelo IA en el micro-lote

# Función ForEachBatch Multi-Destino
def write_analytics(batch_df, batch_id):
    db_args = {"user": "admin", "password": "admin123", "driver": "org.postgresql.Driver"}
    
    # Destino A: BD Operacional (Esto se queda igual)
    batch_df.select(col("maquina").alias("id_sensor"), col("t_avg").alias("valor_promedio"), 
                    col("v_avg").alias("valor_maximo"), col("window.end").alias("timestamp_ventana"), col("decision_id")) \
        .write.jdbc("jdbc:postgresql://iot-postgres:5432/industria40", "predicciones_ia_ventanas", "append", db_args)
    
    # Destino B: Data Lake (AQUÍ ESTÁ EL CAMBIO)
    # coalesce(1) fuerza a Spark a escribir 1 solo archivo por lote en lugar de múltiples

    # Agregamos columnas de fecha para el particionado
    df_para_lake = batch_df.withColumn("year", year(col("window.end"))) \
                           .withColumn("month", month(col("window.end"))) \
                           .withColumn("day", dayofmonth(col("window.end")))

    # Guardamos usando partitionBy
    # Esto creará carpetas como: /year=2026/month=04/day=22/
    df_para_lake.coalesce(1).write.mode("append") \
        .partitionBy("year", "month", "day") \
        .parquet("s3a://datasets/historico_planta/")
    
    batch_df.coalesce(1).write.mode("append").parquet("s3a://datasets/historico_planta/")

analytics_query = windowed_df.writeStream \
    .foreachBatch(write_analytics) \
    .trigger(processingTime="30 seconds") \
    .start()

# Mantiene el proceso vivo escuchando indefinidamente
spark.streams.awaitAnyTermination()