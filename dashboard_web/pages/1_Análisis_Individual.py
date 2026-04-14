import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time

st.set_page_config(page_title="Detalle de Activo", layout="wide")
API_URL = "http://api-servicio:8000/api"

st.sidebar.header("Selección de Activo")
maquina = st.sidebar.selectbox("Máquina a inspeccionar:", [f"M-{str(i).zfill(3)}" for i in range(1, 21)])

st.markdown(f"<h1 style='color: #2b7a8c;'>🔬 Análisis Forense: {maquina}</h1>", unsafe_allow_html=True)
st.markdown("**Nota:** Los indicadores reflejan la consolidación (promedio) de la última ventana de 60 segundos procesada por Spark, eliminando picos falsos o 'ruido' de los sensores.")

try:
    res = requests.get(f"{API_URL}/telemetria/{maquina}")
    if res.status_code == 200 and res.json():
        df = pd.DataFrame(res.json())
        
        ultima_lectura = df.iloc[-1] # El último minuto cerrado
        
        # 1. VELOCÍMETROS (Sincronizados con la nueva Simbología)
        st.subheader("Estado Consolidado (Último Minuto)")
        c1, c2, c3 = st.columns(3)
        
        # Velocímetro de Temperatura
        fig_temp = go.Figure(go.Indicator(
            mode = "gauge+number", value = ultima_lectura['temp'], title = {'text': "Temp Promedio (°C)"},
            gauge = {
                'axis': {'range': [0, 120]}, 
                'bar': {'color': "darkgray"}, 
                'steps': [
                    {'range': [0, 60], 'color': "#00CC96"},  # Normal
                    {'range': [60, 90], 'color': "#FFA15A"}, # Riesgo
                    {'range': [90, 120], 'color': "#EF553B"} # Peligro
                ]
            }
        ))
        c1.plotly_chart(fig_temp, use_container_width=True, height=250)
        
        # Velocímetro de Vibración
        fig_vib = go.Figure(go.Indicator(
            mode = "gauge+number", value = ultima_lectura['vib'], title = {'text': "Vib Promedio (Hz)"},
            gauge = {
                'axis': {'range': [0, 50]}, 
                'bar': {'color': "darkgray"}, 
                'steps': [
                    {'range': [0, 20], 'color': "#00CC96"},  # Normal
                    {'range': [20, 30], 'color': "#FFA15A"}, # Riesgo
                    {'range': [30, 50], 'color': "#EF553B"}  # Peligro
                ]
            }
        ))
        c2.plotly_chart(fig_vib, use_container_width=True, height=250)
        
        with c3:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if ultima_lectura['decision'] == 0:
                st.success("✅ Veredicto IA: MÁQUINA SALUDABLE")
            elif ultima_lectura['decision'] == 1:
                st.warning("⚠️ Veredicto IA: ALERTA / RIESGO")
            else:
                st.error("🚨 Veredicto IA: PARADA RECOMENDADA")

        st.divider()

        # 2. GRÁFICO HISTÓRICO (Línea de tiempo de los últimos 15 minutos)
        st.subheader("Línea de Tiempo de Degradación (Últimos 15 min)")
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(x=df['hora'], y=df['temp'], mode='lines+markers', name='Temperatura Media', line=dict(color='#EF553B', width=3)))
        fig_hist.add_trace(go.Scatter(x=df['hora'], y=df['vib'], mode='lines+markers', name='Vibración Media', line=dict(color='#636EFA', width=3)))
        
        # Añadimos líneas punteadas sutiles para marcar el límite de peligro
        fig_hist.add_hline(y=90, line_dash="dot", line_color="#EF553B", annotation_text="Peligro Térmico", annotation_position="bottom right")
        fig_hist.add_hline(y=30, line_dash="dot", line_color="#636EFA", annotation_text="Peligro Mecánico", annotation_position="bottom right")
        
        fig_hist.update_layout(xaxis_title="Hora (Cierre de Ventana)", yaxis_title="Magnitud", hovermode="x unified")
        st.plotly_chart(fig_hist, use_container_width=True)

    else:
        st.info("Aguardando cierre de ventana de Spark para esta máquina...")

except Exception as e:
    st.error("Sincronizando con el cerebro predictivo...")

time.sleep(5)
st.rerun()