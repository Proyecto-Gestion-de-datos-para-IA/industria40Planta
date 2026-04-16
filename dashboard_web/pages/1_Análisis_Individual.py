import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Análisis por Máquina", page_icon="🔍", layout="wide")

API_URL = "http://api-servicio:8000"

st.title("🔍 Análisis Detallado por Máquina")

maquinas = [f"M-{str(i).zfill(3)}" for i in range(1, 21)]
maq_seleccionada = st.selectbox("Seleccione el equipo a inspeccionar:", maquinas)

st.divider()

# --- 1. VELOCÍMETROS (TIEMPO REAL) ---
st.subheader("Lecturas en Tiempo Real")
col_temp, col_vib = st.columns(2)

try:
    res_rt = requests.get(f"{API_URL}/maquinas/tiempo-real/{maq_seleccionada}")
    if res_rt.status_code == 200:
        datos_rt = res_rt.json()
        
        # Separar valores
        val_temp, val_vib = 0, 0
        for d in datos_rt:
            if "TEMP" in d['id_sensor']: val_temp = d['valor']
            if "VIB" in d['id_sensor']: val_vib = d['valor']

        # Velocímetro de Temperatura
        fig_temp = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = val_temp,
            title = {'text': "Temperatura (°C)"},
            gauge = {'axis': {'range': [0, 120]},
                     'bar': {'color': "darkred"},
                     'steps': [
                         {'range': [0, 60], 'color': "lightgreen"},
                         {'range': [60, 85], 'color': "yellow"},
                         {'range': [85, 120], 'color': "red"}]}
        ))
        col_temp.plotly_chart(fig_temp, use_container_width=True)

        # Velocímetro de Vibración
        fig_vib = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = val_vib,
            title = {'text': "Vibración (Hz)"},
            gauge = {'axis': {'range': [0, 80]},
                     'bar': {'color': "darkblue"},
                     'steps': [
                         {'range': [0, 20], 'color': "lightgreen"},
                         {'range': [20, 40], 'color': "yellow"},
                         {'range': [40, 80], 'color': "red"}]}
        ))
        col_vib.plotly_chart(fig_vib, use_container_width=True)
    else:
        st.warning("Esperando datos en tiempo real de los sensores...")
except Exception as e:
    st.error(f"Error conectando con la API en tiempo real: {e}")

st.divider()

# --- 2. GRÁFICO DE TENDENCIAS (HISTORIAL DE LA IA) ---
st.subheader("Historial de Predicciones IA (Últimos 30 minutos)")

try:
    res_hist = requests.get(f"{API_URL}/maquinas/historial/{maq_seleccionada}")
    if res_hist.status_code == 200:
        historial = res_hist.json()
        if historial:
            df = pd.DataFrame(historial)
            df['timestamp_ventana'] = pd.to_datetime(df['timestamp_ventana'])
            df = df.sort_values('timestamp_ventana')

            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(x=df['timestamp_ventana'], y=df['valor_promedio'], 
                                          mode='lines+markers', name='Temp. Promedio (°C)', line=dict(color='red')))
            fig_hist.add_trace(go.Scatter(x=df['timestamp_ventana'], y=df['valor_maximo'], 
                                          mode='lines+markers', name='Vibración Promedio (Hz)', line=dict(color='blue')))
            
            fig_hist.update_layout(xaxis_title="Tiempo", yaxis_title="Valores", hovermode="x unified")
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No hay suficiente historial procesado por la IA todavía. Espere unos minutos.")
except Exception as e:
    st.error(f"Error obteniendo el historial analítico: {e}")

st.empty()
time.sleep(3)
st.rerun()