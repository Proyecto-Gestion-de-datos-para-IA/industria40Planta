import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Análisis por Máquina", page_icon="🔍", layout="wide")
API_URL = "http://api-servicio:8000"

st.title("🔍 Análisis Detallado y Termografía")
maquinas = [f"M-{str(i).zfill(3)}" for i in range(1, 21)]
maq_seleccionada = st.selectbox("Seleccione el equipo a inspeccionar:", maquinas)

st.divider()

# --- 1. VELOCÍMETROS Y MAPA DE CALOR (TIEMPO REAL) ---
st.subheader("Sensores en Tiempo Real")
col_temp, col_vib, col_calor = st.columns([1, 1, 2])

try:
    res_rt = requests.get(f"{API_URL}/maquinas/tiempo-real/{maq_seleccionada}")
    if res_rt.status_code == 200:
        datos_rt = res_rt.json()
        
        val_temp, val_vib = 0, 0
        for d in datos_rt:
            if "TEMP" in d['id_sensor']: val_temp = d['valor']
            if "VIB" in d['id_sensor']: val_vib = d['valor']

        with col_temp:
            fig_temp = go.Figure(go.Indicator(
                mode="gauge+number", value=val_temp, title={'text': "Temperatura (°C)"},
                gauge={'axis': {'range': [0, 120]}, 'bar': {'color': "darkred"},
                       'steps': [{'range': [0, 60], 'color': "#8fce00"}, # Verde
                                 {'range': [60, 85], 'color': "#ffcc00"}, # Amarillo
                                 {'range': [85, 120], 'color': "#ff0000"}]} # Rojo
            ))
            st.plotly_chart(fig_temp, use_container_width=True)
            st.caption("🟢 < 60°C (Normal) | 🟡 60-85°C (Precaución) | 🔴 > 85°C (Crítico)")

        with col_vib:
            fig_vib = go.Figure(go.Indicator(
                mode="gauge+number", value=val_vib, title={'text': "Vibración (Hz)"},
                gauge={'axis': {'range': [0, 80]}, 'bar': {'color': "darkblue"},
                       'steps': [{'range': [0, 20], 'color': "#8fce00"}, # Verde
                                 {'range': [20, 40], 'color': "#ffcc00"}, # Amarillo
                                 {'range': [40, 80], 'color': "#ff0000"}]} # Rojo
            ))
            st.plotly_chart(fig_vib, use_container_width=True)
            st.caption("🟢 < 20 Hz (Normal) | 🟡 20-40 Hz (Precaución) | 🔴 > 40 Hz (Crítico)")
            
        with col_calor:
            base_map = np.random.normal(val_temp, 2, (5, 5))
            if val_temp > 70: base_map[2, 2] += (val_temp * 0.2) # Concentrar calor
            fig_calor = px.imshow(base_map, color_continuous_scale='RdYlBu_r', origin='lower',
                                  labels=dict(color="Temp °C"), title="Mapa Térmico de Superficie")
            st.plotly_chart(fig_calor, use_container_width=True)
            st.caption("🔍 Representación termográfica simulada (matriz 5x5) basada en la temperatura central.")
            
except Exception as e:
    st.warning(f"Esperando datos en tiempo real de los sensores... ({e})")

st.divider()

# --- 2. GRÁFICO HISTÓRICO (VENTANAS IA) ---
st.subheader("📈 Historial de Predicciones IA (Últimos 30 minutos)")
try:
    res_hist = requests.get(f"{API_URL}/maquinas/historial/{maq_seleccionada}")
    
    if res_hist.status_code == 200:
        historial = res_hist.json()
        if historial and len(historial) > 0:
            df = pd.DataFrame(historial)
            df['timestamp_ventana'] = pd.to_datetime(df['timestamp_ventana'])
            df = df.sort_values('timestamp_ventana')

            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(x=df['timestamp_ventana'], y=df['valor_promedio'], mode='lines+markers', name='Temp. Promedio (°C)', line=dict(color='red')))
            fig_hist.add_trace(go.Scatter(x=df['timestamp_ventana'], y=df['valor_maximo'], mode='lines+markers', name='Vibración Promedio (Hz)', line=dict(color='blue')))
            fig_hist.update_layout(xaxis_title="Hora de Medición", yaxis_title="Valores", hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
            
            st.plotly_chart(fig_hist, use_container_width=True)
            st.caption("💡 Este gráfico muestra el resumen por minuto que realiza la Inteligencia Artificial (Spark).")
        else:
            st.info("Aún no hay ventanas procesadas por Spark para esta máquina. Espere un minuto.")
    else:
        st.error(f"Error de la API: Código {res_hist.status_code}")
except Exception as e:
    st.error(f"Error conectando con la API para el historial: {e}")

st.empty()
time.sleep(5)
st.rerun()