import os
import joblib
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, when, split, concat_ws, udf
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType, IntegerType

# --- CONFIGURACIÓN ---
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 pyspark-shell'

spark = SparkSession.builder \
    .appName("Industria40_Decision_Engine") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Cargamos el cerebro (espera Temp y Vib)
modelo = joblib.load('modelo_falla.pkl')

schema = StructType() \
    .add("id_sensor", StringType()) \
    .add("valor", DoubleType()) \
    .add("timestamp", StringType())

# --- LÓGICA DE PREDICCIÓN MULTIVARIABLE ---
def evaluar_semaforo(t_avg, v_avg):
    # Si por alguna razón falta un sensor en ese minuto, asumimos normalidad
    if t_avg is None or v_avg is None:
        return 0
    # Le pasamos los 2 ingredientes al modelo
    pred = modelo.predict([[t_avg, v_avg]])
    return int(pred[0])

semaforo_udf = udf(evaluar_semaforo, IntegerType())

# --- LECTURA KAFKA ---
raw_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "telemetria_sensores") \
    .load()

telemetria_df = raw_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("timestamp", col("timestamp").cast(TimestampType()))

# --- EL PIVOT (UNIR TEMP Y VIB POR MÁQUINA) ---
# Cortamos "S-TEMP-M-001" para saber qué tipo de sensor es y a qué máquina pertenece
parsed_df = telemetria_df \
    .withColumn("tipo_sensor", split(col("id_sensor"), "-").getItem(1)) \
    .withColumn("maquina", concat_ws("-", split(col("id_sensor"), "-").getItem(2), split(col("id_sensor"), "-").getItem(3)))

windowed_df = parsed_df \
    .withWatermark("timestamp", "10 seconds") \
    .groupBy(
        window(col("timestamp"), "1 minute"),
        col("maquina")
    ) \
    .agg(
        # Calculamos el promedio de cada uno por separado en la misma fila
        avg(when(col("tipo_sensor") == "TEMP", col("valor"))).alias("temp_avg"),
        avg(when(col("tipo_sensor") == "VIB", col("valor"))).alias("vib_avg")
    )

# --- PREDICCIÓN Y ADAPTACIÓN PARA POSTGRES ---
final_df = windowed_df \
    .withColumn("decision_id", semaforo_udf(col("temp_avg"), col("vib_avg"))) \
    .withColumn("timestamp_ventana", col("window.end")) \
    .drop("window") \
    .select(
        col("maquina").alias("id_sensor"),
        col("temp_avg").alias("valor_promedio"), # Mapeamos a la estructura de tu BD
        col("vib_avg").alias("valor_maximo"),    # Mapeamos a la estructura de tu BD
        col("timestamp_ventana"),
        col("decision_id")
    )

def write_to_postgres(batch_df, batch_id):
    url = "jdbc:postgresql://iot-postgres:5432/industria40"
    auth = {"user": "admin", "password": "admin123", "driver": "org.postgresql.Driver"}
    batch_df.write.jdbc(url, "predicciones_ia_ventanas", "append", auth)

query = final_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("update") \
    .start()

print("Motor de Decisión Multivariable iniciado. Procesando ventanas de 1 minuto...")
query.awaitTermination()