import os
import joblib
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, when, split, concat_ws, udf
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType, IntegerType

# Configuración de paquetes
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 pyspark-shell'

spark = SparkSession.builder.appName("Industria40_Full_Engine").getOrCreate()

# Configuración MinIO
sc = spark.sparkContext
sc._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://minio:9000")
sc._jsc.hadoopConfiguration().set("fs.s3a.access.key", "admin")
sc._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "Industria40_Secure")
sc._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
sc._jsc.hadoopConfiguration().set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")

modelo = joblib.load('modelo_falla.pkl')
semaforo_udf = udf(lambda t, v: int(modelo.predict([[t, v]])[0]), IntegerType())

schema = StructType().add("id_sensor", StringType()).add("valor", DoubleType()).add("timestamp", StringType())

# 1. LECTURA DE KAFKA
raw_stream = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "kafka:9092").option("subscribe", "telemetria_sensores").load()

parsed_stream = raw_stream.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*") \
    .withColumn("timestamp", col("timestamp").cast(TimestampType()))

# 2. SALIDA A: telemetria_limpia (Datos Crudos para Velocímetros)
def write_raw(batch_df, batch_id):
    db_args = {"user": "admin", "password": "admin123", "driver": "org.postgresql.Driver"}
    batch_df.select(col("id_sensor"), col("valor"), col("timestamp").alias("timestamp_evento")) \
        .write.jdbc("jdbc:postgresql://iot-postgres:5432/industria40", "telemetria_limpia", "append", db_args)

raw_query = parsed_stream.writeStream.foreachBatch(write_raw).start()

# 3. PROCESAMIENTO DE VENTANAS (Para Dashboards y MinIO)
windowed_df = parsed_stream.withWatermark("timestamp", "10 seconds") \
    .withColumn("maquina", concat_ws("-", split(col("id_sensor"), "-").getItem(2), split(col("id_sensor"), "-").getItem(3))) \
    .groupBy(window(col("timestamp"), "1 minute"), col("maquina")) \
    .agg(avg(when(col("id_sensor").contains("TEMP"), col("valor"))).alias("t_avg"),
         avg(when(col("id_sensor").contains("VIB"), col("valor"))).alias("v_avg")) \
    .withColumn("decision_id", semaforo_udf(col("t_avg"), col("v_avg")))

def write_analytics(batch_df, batch_id):
    db_args = {"user": "admin", "password": "admin123", "driver": "org.postgresql.Driver"}
    # Guardar en Postgres (predicciones_ia_ventanas)
    batch_df.select(col("maquina").alias("id_sensor"), col("t_avg").alias("valor_promedio"), 
                    col("v_avg").alias("valor_maximo"), col("window.end").alias("timestamp_ventana"), col("decision_id")) \
        .write.jdbc("jdbc:postgresql://iot-postgres:5432/industria40", "predicciones_ia_ventanas", "append", db_args)
    # Guardar en MinIO
    batch_df.write.mode("append").parquet("s3a://datasets/historico_planta/")

analytics_query = windowed_df.writeStream.foreachBatch(write_analytics).start()

spark.streams.awaitAnyTermination()