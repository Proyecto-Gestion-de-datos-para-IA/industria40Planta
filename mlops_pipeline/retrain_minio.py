import pandas as pd
import psycopg2
from minio import Minio
from sklearn.ensemble import RandomForestClassifier
import joblib
import io
from datetime import datetime

print("🔄 Iniciando Pipeline MLOps...")

print("1️⃣ Conectando a PostgreSQL...")
conn = psycopg2.connect(host="localhost", port="5432", dbname="industria40", user="admin", password="admin123")
query = "SELECT valor_promedio as temp_avg, valor_maximo as vib_avg, decision_id as label FROM predicciones_ia_ventanas;"
df = pd.read_sql(query, conn)
conn.close()

# Limpiar las filas de MÁQUINAS APAGADAS (Para no confundir a la IA)
df = df[df['temp_avg'] > 25]

print("2️⃣ Conectando a MinIO (Data Lake)...")
cliente_minio = Minio("localhost:9000", access_key="admin", secret_key="Industria40_Secure", secure=False)

for bucket in ["datasets", "modelos"]:
    if not cliente_minio.bucket_exists(bucket):
        cliente_minio.make_bucket(bucket)

timestamp_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
nombre_dataset = f"historico_limpio_{timestamp_actual}.csv"

csv_bytes = df.to_csv(index=False).encode('utf-8')
cliente_minio.put_object("datasets", nombre_dataset, io.BytesIO(csv_bytes), len(csv_bytes))
print(f"💾 Dataset '{nombre_dataset}' respaldado.")

print("3️⃣ Entrenando Cerebro V2 (Random Forest)...")
X = df[['temp_avg', 'vib_avg']]
y = df['label']

modelo_v2 = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
modelo_v2.fit(X, y)

joblib.dump(modelo_v2, 'modelo_falla_v2.pkl')
with open('modelo_falla_v2.pkl', 'rb') as file_data:
    file_stat = io.BytesIO(file_data.read())
    cliente_minio.put_object("modelos", f"modelo_v2_{timestamp_actual}.pkl", file_stat, file_stat.getbuffer().nbytes)

print("🚀 ¡MLOps completado! Nuevo modelo almacenado.")