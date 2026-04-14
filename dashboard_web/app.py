import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Planta 4.0 - Predictivo", page_icon="🏭", layout="wide")
API_URL = "http://api-servicio:8000/api"

st.markdown("<h1 style='text-align: center; color: #2b7a8c;'>🌐 Matriz de Decisión IA - Planta Completa</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Motor de evaluación basado en ventanas consolidadas de 60 segundos.</p>", unsafe_allow_html=True)
st.divider()

with st.expander("ℹ️ Parámetros de Control y Simbología IA", expanded=True):
    st.markdown("<p style='font-size:0.9rem; color:gray;'>El motor evalúa promedios móviles de 60 segundos bajo los siguientes umbrales operativos:</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown("🟢 **NORMAL (0):**<br>🌡️ Temp: `< 60°C`<br>📳 Vib: `< 20 Hz`", unsafe_allow_html=True)
    c2.markdown("🟡 **RIESGO (1):**<br>🌡️ Temp: `60°C - 90°C`<br>📳 Vib: `20 Hz - 30 Hz`", unsafe_allow_html=True)
    c3.markdown("🔴 **PELIGRO (2):**<br>🌡️ Temp: `> 90°C`<br>📳 Vib: `> 30 Hz`", unsafe_allow_html=True)
st.write("")

def crear_donut_semaforo(temp, maq_id, decision):
    # Lógica del Semáforo IA
    if decision == 0:
        color = '#00CC96' # 🟢 Normal
        estado_txt = "NORMAL"
    elif decision == 1:
        color = '#FFA15A' # 🟡 Fricción / Riesgo
        estado_txt = "RIESGO"
    else:
        color = '#EF553B' # 🔴 Falla / Peligro
        estado_txt = "PELIGRO"

    fig = go.Figure(go.Pie(
        values=[temp, max(0, 100-temp)], hole=0.7,
        marker_colors=[color, '#1e1e1e'], textinfo='none', hoverinfo='none'
    ))
    fig.update_layout(
        showlegend=False, margin=dict(t=0, b=0, l=10, r=10), height=140,
        annotations=[dict(text=f"{maq_id}", x=0.5, y=0.5, showarrow=False, font_size=18, font_color=color)]
    )
    return fig, estado_txt, color

# --- LECTURA DE LA API ---
try:
    res = requests.get(f"{API_URL}/planta/estado_ventanas")
    if res.status_code == 200:
        datos = res.json()
        
        if datos:
            df = pd.DataFrame(datos)
            # Aseguramos que se ordenen de la M-001 a la M-020
            df = df.sort_values('id_maquina').reset_index(drop=True)
            
            # --- RENDERIZADO DE LA MATRIZ (4 Filas x 5 Columnas) ---
            for i in range(0, len(df), 5):
                cols = st.columns(5)
                for j in range(5):
                    if i + j < len(df):
                        row = df.iloc[i + j]
                        maq_id = row['id_maquina'].split('-')[-1] # Extrae "001" de "M-001"
                        
                        with cols[j]:
                            with st.container(border=True):
                                # Gráfico
                                fig, estado_txt, color_hex = crear_donut_semaforo(row['temp_promedio'], maq_id, row['decision_ia'])
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                                
                                # Textos de estado
                                st.markdown(f"<p style='text-align:center; color:{color_hex}; font-weight:bold; font-size:1.1rem; margin-bottom:0;'>{estado_txt}</p>", unsafe_allow_html=True)
                                st.markdown(f"<p style='text-align:center; font-size: 0.8rem; color:gray;'>🌡️ {row['temp_promedio']}°C | 📳 {row['vib_promedio']}Hz</p>", unsafe_allow_html=True)
        else:
            st.info("⏳ Esperando a que el motor Spark procese la primera ventana de tiempo (60s)...")
            
except Exception as e:
    st.error(f"Error de conexión con el servidor backend: {e}")

# --- MOTOR EN TIEMPO REAL ---
time.sleep(5) # Consulta a la API cada 5 segundos
st.rerun()