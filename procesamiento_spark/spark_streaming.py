import os
import joblib
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, when, split, concat_ws, udf
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType, IntegerType

# --- CONFIGURACIÓN DE PAQUETES (KAFKA, POSTGRES Y AWS PARA MINIO) ---
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 pyspark-shell'

spark = SparkSession.builder \
    .appName("Industria40_Decision_Engine") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# --- CONFIGURACIÓN MINIO S3 ---
sc = spark.sparkContext
sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://minio:9000")
sc._jsc.hadoopConfiguration().set("fs.s3a.access.key", "admin")
sc._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "Industria40_Secure")
sc._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
sc._jsc.hadoopConfiguration().set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

modelo = joblib.load('modelo_falla.pkl')

schema = StructType() \
    .add("id_sensor", StringType()) \
    .add("valor", DoubleType()) \
    .add("timestamp", StringType())

def evaluar_semaforo(t_avg, v_avg):
    if t_avg is None or v_avg is None:
        return 0
    pred = modelo.predict([[t_avg, v_avg]])
    return int(pred[0])

semaforo_udf = udf(evaluar_semaforo, IntegerType())

raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "telemetria_sensores") \
    .load()

telemetria_df = raw_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("timestamp", col("timestamp").cast(TimestampType()))

parsed_df = telemetria_df \
    .withColumn("tipo_sensor", split(col("id_sensor"), "-").getItem(1)) \
    .withColumn("maquina", concat_ws("-", split(col("id_sensor"), "-").getItem(2), split(col("id_sensor"), "-").getItem(3)))

windowed_df = parsed_df \
    .withWatermark("timestamp", "10 seconds") \
    .groupBy(window(col("timestamp"), "1 minute"), col("maquina")) \
    .agg(
        avg(when(col("tipo_sensor") == "TEMP", col("valor"))).alias("temp_avg"),
        avg(when(col("tipo_sensor") == "VIB", col("valor"))).alias("vib_avg")
    )

final_df = windowed_df \
    .withColumn("decision_id", semaforo_udf(col("temp_avg"), col("vib_avg"))) \
    .withColumn("timestamp_ventana", col("window.end")) \
    .drop("window") \
    .select(
        col("maquina").alias("id_sensor"),
        col("temp_avg").alias("valor_promedio"),
        col("vib_avg").alias("valor_maximo"),
        col("timestamp_ventana"),
        col("decision_id")
    )

def write_to_sinks(batch_df, batch_id):
    # Sink 1: PostgreSQL
    url_db = "jdbc:postgresql://iot-postgres:5432/industria40"
    auth = {"user": "admin", "password": "admin123", "driver": "org.postgresql.Driver"}
    try:
        batch_df.write.jdbc(url_db, "predicciones_ia_ventanas", "append", auth)
    except Exception as e:
        print(f"Error escribiendo en Postgres: {e}")
        
    # Sink 2: MinIO (Parquet)
    try:
        batch_df.write.mode("append").parquet("s3a://datasets/historico_planta/")
    except Exception as e:
        print(f"Error escribiendo en MinIO: {e}")

query = final_df.writeStream \
    .foreachBatch(write_to_sinks) \
    .outputMode("update") \
    .start()

print("Motor Iniciado: Procesando telemetría hacia Postgres y MinIO...")
query.awaitTermination()