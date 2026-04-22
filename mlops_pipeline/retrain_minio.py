import pandas as pd
import s3fs
import joblib
from sklearn.ensemble import RandomForestClassifier

print("🔄 Iniciando Pipeline MLOps: Reentrenamiento desde Data Lake...")

try:
    # CORRECCIÓN 1: Conectar al puerto API (9000)
    fs = s3fs.S3FileSystem(client_kwargs={'endpoint_url': 'http://localhost:9000'}, key='admin', secret='Industria40_Secure')
    archivos = fs.glob('datasets/historico_planta/*.parquet')
    
    if not archivos:
        print("❌ No hay datos en el Data Lake. Asegúrate de que Spark esté corriendo.")
        exit()
        
    print(f"📥 Leyendo {len(archivos)} lotes históricos de MinIO...")
    
    # CORRECCIÓN 2: Puerto API (9000) también en pandas
    df = pd.concat([pd.read_parquet(f"s3://{f}", storage_options={'client_kwargs': {'endpoint_url': 'http://localhost:9000'}, 'key': 'admin', 'secret': 'Industria40_Secure'}) for f in archivos])
    
    print(f"📊 Se recuperaron {len(df)} registros históricos del Data Lake.")
    
    # Usar los nombres reales de las columnas en MinIO
    X = df[['t_avg', 'v_avg']]
    y = df['decision_id']
    
    print("🧠 Entrenando nuevo modelo RandomForest...")
    modelo_nuevo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo_nuevo.fit(X, y)
    
    # Sobrescribimos el modelo local para que Spark lo use
    joblib.dump(modelo_nuevo, 'modelo_falla.pkl')
    print("✅ ¡Pipeline exitoso! Modelo 'modelo_falla.pkl' actualizado con nueva inteligencia.")

except Exception as e:
    print(f"❌ Error crítico en el pipeline: {e}")