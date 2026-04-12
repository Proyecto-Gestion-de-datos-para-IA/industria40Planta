import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time

st.set_page_config(page_title="Detalle de Activo", layout="wide")
API_URL = "http://api-backend:8000/api"

st.sidebar.header("Selección de Activo")
maquina = st.sidebar.selectbox("Máquina:", [f"M-{str(i).zfill(3)}" for i in range(1, 21)])

st.markdown(f"<h1 style='color: #2b7a8c;'>🔍 Análisis Técnico: {maquina}</h1>", unsafe_allow_html=True)

try:
    res = requests.get(f"{API_URL}/telemetria/{maquina}")
    if res.status_code == 200:
        df = pd.DataFrame(res.json())
        df_t = df[df['id_sensor'].str.contains("TEMP")]
        df_v = df[df['id_sensor'].str.contains("VIB")]

        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.metric("Temperatura Actual", f"{df_t['valor_leido'].iloc[-1]:.1f} °C")
            # Gráfico de línea solo para esta máquina
            fig_t = go.Figure(go.Scatter(x=df_t['timestamp_prediccion'], y=df_t['valor_leido'], name="Temp", line=dict(color="#FF5733")))
            fig_t.update_layout(height=250, margin=dict(t=0, b=0), yaxis_range=[0,100])
            st.plotly_chart(fig_t, use_container_width=True)

        with col2:
            st.metric("Vibración Actual", f"{df_v['valor_leido'].iloc[-1]:.1f} Hz")
            fig_v = go.Figure(go.Scatter(x=df_v['timestamp_prediccion'], y=df_v['valor_leido'], name="Vib", line=dict(color="#33C1FF")))
            fig_v.update_layout(height=250, margin=dict(t=0, b=0), yaxis_range=[0,40])
            st.plotly_chart(fig_v, use_container_width=True)

        with col3:
            st.subheader("📋 Ficha de Estado")
            estado = "🔴 CRÍTICO" if (df_t['falla_predicha'].iloc[-1] == 1 or df_v['falla_predicha'].iloc[-1] == 1) else "🟢 NORMAL"
            st.write(f"**Veredicto IA:** {estado}")
            st.write(f"**Máximo Calor:** {df_t['valor_leido'].max():.1f} °C")
            st.write(f"**Promedio Vibración:** {df_v['valor_leido'].mean():.1f} Hz")

except Exception as e:
    st.warning("Cargando datos...")

time.sleep(2)
st.rerun()