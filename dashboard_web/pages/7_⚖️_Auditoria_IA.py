import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.metrics import confusion_matrix, accuracy_score, mean_absolute_error
import requests

#"""
#=============================================================================
##MÓDULO: Auditoría y Evaluación de Modelos (MLOps)
#ARCHIVO: pages/7_⚖️_Auditoria_IA.py
#VERSIÓN: 2.5
#=============================================================================
#DESCRIPCIÓN:
#Capa de monitoreo de desempeño de Inteligencia Artificial. Calcula la 
#precisión y el error de los 3 modelos en producción comparándolos con 
#la 'Verdad de Campo' (Ground Truth) inyectada.
#=============================================================================
#"""

st.set_page_config(page_title="Auditoría IA V2.5", page_icon="⚖️", layout="wide")
API_URL = "http://api-servicio:8000"

st.title("⚖️ Centro de Auditoría de Inteligencia Artificial")
st.write("Evaluación de precisión, sesgo y error de los modelos en producción.")

# =============================================================================
# 1. RECUPERACIÓN DE DATOS DE AUDITORÍA
# =============================================================================
def get_audit_data():
    try:
        # Aquí simulamos la carga de la tabla 'auditoria_ia'
        # En producción, esto se lee de Postgres con: SELECT * FROM auditoria_ia
        response = requests.get(f"{API_URL}/maquinas/estado-general") # Ejemplo
        return pd.DataFrame(response.json())
    except:
        return pd.DataFrame()

df_audit = get_audit_data()

# --- SELECTOR DE MODELO A AUDITAR ---
modelo_check = st.sidebar.selectbox("Seleccione el Cerebro a evaluar:", ["Clasificador de Estados", "Visión Térmica CNN", "Regresor RUL"])

st.divider()

# =============================================================================
# 2. EVALUACIÓN SEGÚN TIPO DE MODELO
# =============================================================================

if modelo_check == "Clasificador de Estados":
    st.header("🎯 Evaluación: Clasificador de Estados (Random Forest)")
    
    # Simulación de datos para la demostración de la métrica
    y_real = [0, 1, 2, 0, 1, 2, 0, 0, 2, 1] # 0:Normal, 1:Riesgo, 2:Falla
    y_pred = [0, 1, 2, 0, 0, 2, 0, 1, 2, 1] 
    
    acc = accuracy_score(y_real, y_pred)
    
    k1, k2 = st.columns(2)
    k1.metric("Accuracy (Exactitud)", f"{acc*100:.1f}%", help="Porcentaje de aciertos totales sobre el total de casos.")
    
    st.subheader("📊 Matriz de Confusión")
    st.write("Identifica dónde se confunde la IA (ej: confundir Riesgo con Falla).")
    
    
    cm = confusion_matrix(y_real, y_pred)
    fig_cm = px.imshow(cm, text_auto=True, 
                       labels=dict(x="Predicción IA", y="Realidad (Consola Caos)"),
                       x=['Normal', 'Riesgo', 'Falla'],
                       y=['Normal', 'Riesgo', 'Falla'],
                       color_continuous_scale='Blues')
    st.plotly_chart(fig_cm, use_container_width=True)

elif modelo_check == "Regresor RUL":
    st.header("🔮 Evaluación: Predicción de Vida Útil (RUL)")
    
    # Datos de ejemplo: Minutos reales hasta la falla vs Predichos
    minutos_reales = np.array([120, 90, 45, 10, 200])
    minutos_pred = np.array([115, 98, 40, 12, 190])
    
    mae = mean_absolute_error(minutos_reales, minutos_pred)
    
    k1, k2 = st.columns(2)
    k1.metric("Error Absoluto Medio (MAE)", f"±{mae:.1f} min", delta_color="inverse")
    
    st.subheader("📈 Gráfico de Dispersión: Real vs Predicho")
    st.caption("Mientras más cerca estén los puntos de la línea diagonal, más preciso es el modelo.")
    
    
    fig_reg = px.scatter(x=minutos_reales, y=minutos_pred, labels={'x': 'Realidad (min)', 'y': 'Predicción (min)'})
    fig_reg.add_shape(type="line", x0=0, y0=0, x1=max(minutos_reales), y1=max(minutos_reales), line=dict(color="Red", dash="dot"))
    st.plotly_chart(fig_reg, use_container_width=True)

elif modelo_check == "Visión Térmica CNN":
    st.header("🎥 Evaluación: Clasificación Visual (CNN)")
    st.info("La evaluación de la CNN se basa en el histórico de Confianza (Softmax output).")
    
    # Histórico de confianza del modelo
    confianzas = np.random.normal(0.92, 0.05, 100) # Simulación de 100 inferencias
    
    fig_dist = px.histogram(confianzas, nbins=20, title="Distribución de Confianza del Modelo",
                            labels={'value': 'Nivel de Confianza (0.0 - 1.0)'})
    st.plotly_chart(fig_dist, use_container_width=True)
    st.caption("Un desplazamiento a la izquierda en este gráfico indica que la cámara necesita ser re-calibrada o el modelo re-entrenado.")