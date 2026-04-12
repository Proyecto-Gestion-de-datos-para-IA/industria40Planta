import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time

st.set_page_config(page_title="Planta 4.0 - Global", layout="wide")
API_URL = "http://api-backend:8000/api"

# Cabecera fija
st.markdown("<h1 style='text-align: center; color: #2b7a8c;'>🌐 Panel de Control Global - Planta</h1>", unsafe_allow_html=True)
st.divider()

def crear_donut_simple(valor, maq_id, falla):
    color = '#EF553B' if falla == 1 else '#00CC96'
    fig = go.Figure(go.Pie(
        values=[valor, 100-valor], hole=0.7,
        marker_colors=[color, '#e6e6e6'], textinfo='none', hoverinfo='none'
    ))
    fig.update_layout(
        showlegend=False, margin=dict(t=0, b=0, l=10, r=10), height=140,
        annotations=[dict(text=f"{maq_id}", x=0.5, y=0.5, showarrow=False, font_size=16)]
    )
    return fig

try:
    res = requests.get(f"{API_URL}/planta/estado_actual")
    if res.status_code == 200:
        df = pd.DataFrame(res.json())
        
        # Filtramos solo Temperaturas para el resumen rápido
        df_t = df[df['id_sensor'].str.contains("TEMP")].copy()
        
        # Grid de 4x5 para mostrar las 20 máquinas
        for i in range(0, len(df_t), 5):
            cols = st.columns(5)
            for j in range(5):
                if i + j < len(df_t):
                    row = df_t.iloc[i + j]
                    maq_id = row['id_sensor'].split('-')[-1]
                    with cols[j]:
                        st.plotly_chart(crear_donut_simple(row['valor_leido'], maq_id, row['falla_predicha']), use_container_width=True)
                        # El texto de alerta ahora está condicionado al valor REAL
                        if row['falla_predicha'] == 1:
                            st.markdown(f"<p style='text-align:center; color:#EF553B; font-weight:bold;'>⚠️ ALERTA</p>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<p style='text-align:center; color:#00CC96;'>✅ OK</p>", unsafe_allow_html=True)

    st.divider()
    st.subheader("📊 Resumen de Alertas (Últimos 10 min)")
    res_h = requests.get(f"{API_URL}/planta/historico_10m")
    if res_h.status_code == 200:
        df_h = pd.DataFrame(res_h.json())
        if not df_h.empty:
            st.bar_chart(df_h.set_index('id_maquina')['total_fallas'])

except Exception as e:
    st.error("Conectando con la API...")

time.sleep(2)
st.rerun()