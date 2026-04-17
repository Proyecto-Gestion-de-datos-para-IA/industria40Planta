import streamlit as st
import requests
import numpy as np
import plotly.express as px
import time

st.title("🔍 Análisis y Mapa de Calor")
maquina = st.selectbox("Máquina:", [f"M-{str(i).zfill(3)}" for i in range(1, 21)])

API_URL = "http://api-servicio:8000"

# --- SIMULACIÓN DE MAPA DE CALOR ---
st.subheader(f"🔥 Mapa Térmico de Superficie - {maquina}")

try:
    res = requests.get(f"{API_URL}/maquinas/tiempo-real/{maquina}").json()
    temp_actual = next((d['valor'] for d in res if 'TEMP' in d['id_sensor']), 40)
    
    # Generamos una matriz de 5x5 simulando puntos de calor en el motor
    base_map = np.random.normal(temp_actual, 2, (5, 5))
    # Simulamos un "punto caliente" central
    base_map[2, 2] += 10 
    
    fig = px.imshow(base_map, color_continuous_scale='RdYlBu_r', origin='lower',
                    labels=dict(color="Temp °C"), title="Distribución Térmica del Rodamiento")
    st.plotly_chart(fig, use_container_width=True)
    
except:
    st.info("Obteniendo matriz térmica...")

time.sleep(5)
st.rerun()