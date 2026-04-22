import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Análisis Individual V2.5", page_icon="🔍", layout="wide")
API_URL = "http://api-servicio:8000"

st.title("🔍 Análisis de Activo y Diagnóstico IA")

# Selector de Máquinas (Filtro Dinámico)
maquinas = [f"M-{str(i).zfill(3)}" for i in range(1, 21)]
maq_seleccionada = st.selectbox("Seleccione el equipo a inspeccionar:", maquinas, help="El ID seleccionado filtrará las consultas a Postgres y el historial en MinIO.")

st.divider()

# =============================================================================
# SECCIÓN 1: TELEMETRÍA DE ALTA VELOCIDAD (SPEED LAYER)
# =============================================================================
st.subheader("📡 Instrumentación en Tiempo Real")
col_temp, col_vib, col_calor = st.columns([1, 1, 2])



#=============================================================================
#MÓDULO: Análisis Detallado de Activos e Inferencia de Sensores
#ARCHIVO: pages/1_📈_Analisis_Individual.py
#VERSIÓN: 2.5
#=============================================================================
#DESCRIPCIÓN:
#Proporciona una vista profunda de una unidad específica. Combina datos 
#crudos de alta frecuencia (Speed Layer) con promedios procesados por Spark.

#ARQUITECTURA DE DATOS:
#1. Sensores RT: Consulta la tabla 'telemetria_limpia' para visualización instantánea.
#2. Historial IA: Consulta 'predicciones_ia_ventanas' para ver el comportamiento
#   agregado que el modelo Random Forest analizó previamente.
   
#IA & VISIÓN:
#- Gauges: Representación visual de umbrales críticos para entrenamiento supervisado.
#- Termografía: Simulación de mapas de calor para validación de patrones térmicos.
#=============================================================================







def get_realtime_data(machine_id):
    """
    Obtiene las últimas lecturas crudas del bus de datos (vía API).
    Estas lecturas son las 'Features' primarias de los modelos de detección.
    """
    try:
        res = requests.get(f"{API_URL}/maquinas/tiempo-real/{machine_id}", timeout=3)
        return res.json() if res.status_code == 200 else None
    except:
        return None

datos_rt = get_realtime_data(maq_seleccionada)

if datos_rt:
    val_temp, val_vib = 0, 0
    for d in datos_rt:
        if "TEMP" in d['id_sensor']: val_temp = d['valor']
        if "VIB" in d['id_sensor']: val_vib = d['valor']

    with col_temp:
        # Gauge de Temperatura: Monitoreo Térmico Directo
        fig_temp = go.Figure(go.Indicator(
            mode="gauge+number", value=val_temp, title={'text': "Temperatura (°C)"},
            gauge={'axis': {'range': [0, 120]}, 'bar': {'color': "darkred"},
                   'steps': [{'range': [0, 60], 'color': "#8fce00"},
                             {'range': [60, 85], 'color': "#ffcc00"},
                             {'range': [85, 120], 'color': "#ff0000"}]}
        ))
        st.plotly_chart(fig_temp, use_container_width=True)
        st.caption("🟢 < 60°C (Normal) | 🟡 60-85°C (Precaución) | 🔴 > 85°C (Crítico)")

    with col_vib:
        # Gauge de Vibración: Indicador clave de degradación mecánica (RUL)
        fig_vib = go.Figure(go.Indicator(
            mode="gauge+number", value=val_vib, title={'text': "Vibración (Hz)"},
            gauge={'axis': {'range': [0, 80]}, 'bar': {'color': "darkblue"},
                   'steps': [{'range': [0, 20], 'color': "#8fce00"},
                             {'range': [20, 40], 'color': "#ffcc00"},
                             {'range': [40, 80], 'color': "#ff0000"}]}
        ))
        st.plotly_chart(fig_vib, use_container_width=True)
        st.caption("🟢 < 20 Hz (Normal) | 🟡 20-40 Hz (Precaución) | 🔴 > 40 Hz (Crítico)")
        
    with col_calor:
        # Simulación de Visión Térmica: Preparación para modelos CNN de imágenes
        base_map = np.random.normal(val_temp, 2, (5, 5))
        if val_temp > 70: base_map[2, 2] += (val_temp * 0.2) # Algoritmo de hotspot central
        
        fig_calor = px.imshow(base_map, color_continuous_scale='RdYlBu_r', origin='lower',
                              labels=dict(color="Temp °C"), title="Mapa Térmico de Superficie")
        st.plotly_chart(fig_calor, use_container_width=True)
        st.caption("🔍 Simulación de matriz térmica 5x5 para validación de sensores ópticos.")

else:
    st.warning("🔄 Sincronizando con el bus de datos de Kafka... Asegúrese de que el Simulador esté activo.")

st.divider()

# =============================================================================
# SECCIÓN 2: ANALÍTICA AGREGADA E INFERENCIA IA (BATCH LAYER)
# =============================================================================

st.subheader("📈 Historial de Diagnóstico IA (Ventanas de Inferencia)")

def get_historical_analysis(machine_id):
    """
    Recupera el historial de ventanas de 1 minuto procesadas por Spark.
    Proporciona el contexto temporal necesario para modelos predictivos.
    """
    try:
        res = requests.get(f"{API_URL}/maquinas/historial/{machine_id}", timeout=3)
        return res.json() if res.status_code == 200 else []
    except:
        return []

historial = get_historical_analysis(maq_seleccionada)

if historial:
    df = pd.DataFrame(historial)
    df['timestamp_ventana'] = pd.to_datetime(df['timestamp_ventana'])
    df = df.sort_values('timestamp_ventana')

    # Gráfico Multivariable de Tendencias
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(x=df['timestamp_ventana'], y=df['valor_promedio'], 
                                 mode='lines+markers', name='Temp. Promedio (°C)', 
                                 line=dict(color='red', width=2)))
    fig_hist.add_trace(go.Scatter(x=df['timestamp_ventana'], y=df['valor_maximo'], 
                                 mode='lines+markers', name='Vibración Promedio (Hz)', 
                                 line=dict(color='blue', width=2)))
    
    fig_hist.update_layout(
        xaxis_title="Tiempo de Operación", 
        yaxis_title="Unidades de Medida",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    st.plotly_chart(fig_hist, use_container_width=True)
    st.info("💡 Este gráfico representa la 'Verdad de Campo' utilizada por Spark para clasificar el estado de la máquina.")
else:
    st.info("⏳ Esperando el primer lote de datos procesados. Spark requiere al menos 60 segundos de telemetría para generar una ventana.")

# Lógica de actualización de la página
st.empty()
time.sleep(5)
st.rerun()