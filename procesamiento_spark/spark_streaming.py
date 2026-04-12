import os
import joblib
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, pandas_udf
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType, IntegerType

# Con Java 11, solo necesitamos los drivers puros
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 pyspark-shell'

spark = SparkSession.builder.appName("Industria40_Completa").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# ... (Todo tu código de Carga de IA y Guardado sigue exactamente igual)

# CARGA DE IA (Rutas relativas corregidas)
modelo = joblib.load('modelo_falla.pkl')
columnas_entrenamiento = joblib.load('columnas_modelo.pkl')

@pandas_udf(IntegerType())
def predecir_falla_udf(id_sensor_series: pd.Series, valor_medicion_series: pd.Series) -> pd.Series:
    df_temp = pd.DataFrame({'id_sensor': id_sensor_series, 'valor_medicion': valor_medicion_series})
    X = pd.get_dummies(df_temp, columns=['id_sensor'])
    for c in columnas_entrenamiento:
        if c not in X.columns: X[c] = 0
    return pd.Series(modelo.predict(X[columnas_entrenamiento]))

# PROCESAMIENTO
esquema = StructType().add("id_sensor", StringType()).add("timestamp_evento", TimestampType()).add("valor_medicion", DoubleType())

df_kafka = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "iot-kafka:9092").option("subscribe", "telemetria_sensores").load()

df_inteligente = df_kafka.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), esquema).alias("data")).select("data.*") \
    .filter(col("valor_medicion") > -500) \
    .withColumn("falla_predicha", predecir_falla_udf(col("id_sensor"), col("valor_medicion")))

# GUARDADO DOBLE EN POSTGRES
def guardar_tablas(df, epoch_id):
    url = "jdbc:postgresql://iot-postgres:5432/industria40"
    auth = {"user": "admin", "password": "admin123", "driver": "org.postgresql.Driver"}
    
    # 1. Histórico Limpio
    df.select("id_sensor", "timestamp_evento", "valor_medicion") \
      .write.jdbc(url, "telemetria_limpia", "append", auth)
    
    # 2. Predicciones IA
    df.select("id_sensor", col("timestamp_evento").alias("timestamp_prediccion"), 
              col("valor_medicion").alias("valor_leido"), "falla_predicha") \
      .write.jdbc(url, "predicciones_ia", "append", auth)

df_inteligente.writeStream.foreachBatch(guardar_tablas).start()
spark.streams.awaitAnyTermination()