import pandas as pd
from minio import Minio
from sklearn.ensemble import RandomForestClassifier
import joblib
import io
import os
from datetime import datetime

print("🔄 Iniciando Pipeline MLOps: Reentrenamiento desde Data Lake...")

# 1. Configuración de credenciales para Pandas y MinIO
MINIO_ENDPOINT = "localhost:9000" # Si ejecutas esto desde otra PC hacia el VPS, cambia "localhost" por la IP de tu VPS
ACCESS_KEY = "admin"
SECRET_KEY = "Industria40_Secure"

storage_options = {
    "key": ACCESS_KEY,
    "secret": SECRET_KEY,
    "client_kwargs": {"endpoint_url": f"http://{MINIO_ENDPOINT}"}
}

try:
    # 2. Descargar histórico completo
    print("📥 Leyendo histórico de sensores desde MinIO (datasets/historico_planta/)...")
    # Pandas usa s3fs por debajo para leer directamente los archivos Parquet del bucket
    df = pd.read_parquet("s3://datasets/historico_planta/", storage_options=storage_options)
    print(f"📊 Se recuperaron {len(df)} registros históricos del Data Lake.")

    # 3. Limpieza de datos (Filtrar máquinas apagadas)
    # Si la temperatura promedio cae por debajo de 25°C, asumimos que el motor se detuvo
    df_limpio = df[df['valor_promedio'] > 25]
    print(f"🧹 Registros útiles tras descartar máquinas en estado 'APAGADA': {len(df_limpio)}")

    if len(df_limpio) < 50:
        print("⚠️ Advertencia: Hay muy pocos datos para entrenar una IA robusta.")
        print("💡 Ve a tu Consola del Caos, inyecta fallas y espera unos minutos antes de volver a intentar.")
        exit()

    # 4. Entrenamiento del Modelo V2
    print("🧠 Entrenando nuevo Cerebro Industrial (Random Forest V2)...")
    X = df_limpio[['valor_promedio', 'valor_maximo']] # Temperatura y Vibración
    y = df_limpio['decision_id']                      # El semáforo (0, 1 o 2)

    modelo_v2 = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
    modelo_v2.fit(X, y)

    # 5. Guardar modelo y subir a MinIO
    print("💾 Guardando el nuevo modelo versionado...")
    cliente_minio = Minio(MINIO_ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)
    
    # Asegurar que el bucket de modelos exista
    if not cliente_minio.bucket_exists("modelos"):
        cliente_minio.make_bucket("modelos")

    # Generar nombre único con la fecha y hora exactas
    timestamp_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_modelo = f"modelo_v2_{timestamp_actual}.pkl"

    # Exportar el modelo al disco local temporalmente
    joblib.dump(modelo_v2, nombre_modelo)

    # Inyectar el archivo en MinIO
    with open(nombre_modelo, 'rb') as file_data:
        file_stat = io.BytesIO(file_data.read())
        cliente_minio.put_object("modelos", nombre_modelo, file_stat, file_stat.getbuffer().nbytes)

    # Limpiar el archivo local para no dejar basura
    os.remove(nombre_modelo)

    print(f"🚀 ¡Éxito Absoluto! MLOps completado. El archivo '{nombre_modelo}' está seguro en el bucket 'modelos' de MinIO.")

except Exception as e:
    print(f"❌ Error crítico en el pipeline: {e}")
    print("💡 Tip: Verifica que Spark ya haya procesado al menos un minuto de datos y creado la carpeta 'historico_planta' en MinIO.")