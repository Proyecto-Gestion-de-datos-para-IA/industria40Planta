import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

def generar_data_entrenamiento(muestras_por_clase=1000):
    print("Generando datos históricos sintéticos (Gemelo Digital)...")
    data = []
    
    # 1. Datos de Estado NORMAL (Semaforo 0)
    for _ in range(muestras_por_clase):
        t_avg = np.random.normal(40, 2)
        v_avg = np.random.normal(10, 1)
        data.append([t_avg, v_avg, 0])
        
    # 2. Datos de ALERTA / FRICCIÓN (Semaforo 1)
    for _ in range(muestras_por_clase):
        t_avg = np.random.normal(85, 4)
        v_avg = np.random.normal(15, 2)
        data.append([t_avg, v_avg, 1])
        
    # 3. Datos de PELIGRO / DESALINEACIÓN (Semaforo 2)
    for _ in range(muestras_por_clase):
        t_avg = np.random.normal(50, 3)
        v_avg = np.random.normal(35, 4)
        data.append([t_avg, v_avg, 2])
        
    return pd.DataFrame(data, columns=['temp_avg', 'vib_avg', 'label'])

# Generamos el dataset (3000 filas en total)
df = generar_data_entrenamiento()

X = df[['temp_avg', 'vib_avg']]
y = df['label']

print("Entrenando el modelo Random Forest (Clasificación Multiclase)...")
modelo = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=5)
modelo.fit(X, y)

# Guardamos el cerebro de la IA
joblib.dump(modelo, 'modelo_falla.pkl')
print("✅ ¡Éxito! Archivo 'modelo_falla.pkl' generado y listo para Spark.")