import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

"""
=============================================================================
SCRIPT: Entrenamiento de Modelo Predictivo (RUL)
DESCRIPCIÓN: 
Genera un dataset sintético de degradación mecánica y entrena un modelo de 
regresión para predecir los MINUTOS RESTANTES antes de la Falla Crítica.
=============================================================================
"""

print("⚙️ Generando datos históricos de desgaste...")

# Vamos a simular el ciclo de vida de 500 máquinas hasta que se rompen
datos = []

for maquina_id in range(500):
    # Ciclo de vida aleatorio entre 60 y 300 minutos
    vida_total = np.random.randint(60, 300) 
    
    temp_base = 45.0
    vib_base = 10.0
    
    for minuto_actual in range(vida_total):
        rul = vida_total - minuto_actual # Remaining Useful Life (Lo que queremos predecir)
        
        # A medida que se acerca la falla (RUL bajo), la vibración y temperatura suben exponencialmente
        porcentaje_desgaste = minuto_actual / vida_total
        
        temp = temp_base + (np.random.normal(0, 2)) + (porcentaje_desgaste ** 2) * 50
        vib = vib_base + (np.random.normal(0, 1)) + (porcentaje_desgaste ** 3) * 60
        
        datos.append([temp, vib, rul])

# Convertir a DataFrame
df = pd.DataFrame(datos, columns=['Temperatura', 'Vibracion', 'RUL_Minutos'])

print(f"✅ Dataset generado: {len(df)} registros.")
print("🧠 Entrenando modelo Random Forest Regressor...")

# Separar características (X) de la etiqueta a predecir (y)
X = df[['Temperatura', 'Vibracion']]
y = df['RUL_Minutos']

# Entrenar el modelo
# Usamos Regresión porque queremos un número continuo (minutos), no una categoría
modelo_rul = RandomForestRegressor(n_estimators=100, max_depth=10, n_jobs=-1, random_state=42)
modelo_rul.fit(X, y)

print("💾 Guardando el modelo entrenado...")
joblib.dump(modelo_rul, 'modelo_rul.pkl')

print("🚀 ¡Modelo 'modelo_rul.pkl' creado exitosamente! Listo para inyectar en Spark.")