import streamlit as st
import requests
import pandas as pd
import joblib
import plotly.express as px
import plotly.graph_objects as go
import joblib

#"""
#=============================================================================
#MÓDULO: Centro de Predicción de Vida Útil (RUL - Remaining Useful Life)
#RCHIVO: pages/6_🔮_Centro_Predicciones.py
#VERSión: 2.5
#=============================================================================
#DESCRIPCIÓN:
#Capa de Inteligencia Predictiva Avanzada. Utiliza un modelo de regresión
#Random Forest para estimar el tiempo restante de operación segura de cada
#activo basándose en la degradación de sus variables térmicas y mecánicas.

#LÓGICA DE INFERENCIA:
#1. Captura: Obtiene el estado actual (Temp/Vib) desde la Capa de Servicio.
#2. Predicción: Inyecta las variables en el 'modelo_rul.pkl'.
#3. Visualización: Traduce el número crudo en un 'Reloj de Arena' operativo.

#VALOR DE NEGOCIO:
#Optimización del MTBF (Mean Time Between Failures) y reducción de paradas
#no programadas mediante la planificación de intervenciones precisas.
#=============================================================================
#"""

st.set_page_config(page_title="Predicciones RUL V2.5", page_icon="🔮", layout="wide")
API_URL = "http://api-servicio:8000"

# =============================================================================
# 1. CARGA DEL MODELO MATEMÁTICO
# =============================================================================
@st.cache_resource
def cargar_modelo_rul():
    """Carga los pesos del regresor entrenado para estimación de tiempo."""
    try:
        return joblib.load("modelo_rul.pkl")
    except:
        return None

modelo_rul = cargar_modelo_rul()

st.title("🔮 Centro de Predicciones y Salud de Activos")
st.write("Cálculo de Vida Útil Restante (RUL) mediante análisis de degradación en tiempo real.")

if modelo_rul is None:
    st.error("🚨 No se encontró el archivo 'modelo_rul.pkl'. Asegúrate de haber ejecutado el script de entrenamiento y subido el archivo a la carpeta del dashboard.")
    st.stop()

# =============================================================================
# 2. PROCESAMIENTO DE DATOS Y PREDICCIÓN
# =============================================================================
def obtener_predicciones():
    try:
        response = requests.get(f"{API_URL}/maquinas/estado-general", timeout=3)
        data = response.json()

        if not data:
            st.warning("⚠️ La API respondió, pero la lista de máquinas está VACÍA. ¿Está corriendo el simulador?")
            return pd.DataFrame()
        
        resultados = []
        for maq in data:
            # Extraemos las características para el modelo
            # Importante: El orden [Temp, Vib] debe ser igual al del entrenamiento
            features = [[maq['valor_promedio'], maq['valor_maximo']]]
            
            # Realizamos la inferencia (Resultado en minutos)
            minutos_restantes = modelo_rul.predict(features)[0]
            
            # Si la máquina está apagada, la predicción es irrelevante
            if maq['estado_actual'] == "APAGADA":
                minutos_restantes = 0
            
            resultados.append({
                "ID": maq['id_maquina'],
                "Estado": maq['estado_actual'],
                "Temp": maq['valor_promedio'],
                "Vib": maq['valor_maximo'],
                "RUL": round(minutos_restantes, 1)
            })
        return pd.DataFrame(resultados)
    except Exception as e:
        # Esto te dirá exactamente qué falla: si es la URL, el modelo, o los datos
        st.error(f"❌ Error crítico en la predicción: {e}")
        return pd.DataFrame()

df_pred = obtener_predicciones()

# =============================================================================
# 3. INTERFAZ VISUAL: RANKING DE URGENCIAS
# =============================================================================
if not df_pred.empty:
    
    # Ordenar por las máquinas que fallarán más pronto
    df_peligro = df_pred[df_pred['Estado'] != "APAGADA"].sort_values(by="RUL")
    
    st.subheader("⚠️ Próximas Intervenciones Requeridas")
    st.caption("Estimación de tiempo restante basado en la curva de fatiga mecánica detectada.")

    # Mostrar Top 3 máquinas más críticas
    cols = st.columns(3)
    for i in range(min(3, len(df_peligro))):
        maq = df_peligro.iloc[i]
        with cols[i]:
            # Color dinámico según la urgencia
            color_rul = "red" if maq['RUL'] < 30 else "orange" if maq['RUL'] < 100 else "green"
            
            st.markdown(f"""
                <div style="border: 2px solid {color_rul}; padding: 20px; border-radius: 15px; text-align: center; background-color: rgba(0,0,0,0.05);">
                    <h2 style="margin-bottom: 0;">{maq['ID']}</h2>
                    <p style="font-size: 18px; margin-top: 10px;">Falla estimada en:</p>
                    <h1 style="color: {color_rul}; font-size: 50px; margin: 10px 0;">{maq['RUL']} <small style="font-size: 20px;">min</small></h1>
                    <hr>
                    <p style="font-size: 14px; color: gray;">Prioridad de Mantenimiento: <b>{'ALTA' if color_rul == 'red' else 'MEDIA' if color_rul == 'orange' else 'BAJA'}</b></p>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Gráfico Comparativo de Flota
    st.subheader("📊 Comparativa de Vida Útil Restante (Flota Completa)")
    
    fig_rul = px.bar(
        df_pred, 
        x="ID", 
        y="RUL", 
        color="RUL",
        color_continuous_scale="RdYlGn",
        labels={"RUL": "Minutos de Operación Segura"},
        title="Estimación RUL por Activo"
    )
    # Línea de seguridad (Umbral de 30 minutos)
    fig_rul.add_hline(y=30, line_dash="dot", line_color="red", annotation_text="Zona de Peligro")
    
    st.plotly_chart(fig_rul, use_container_width=True)

    # Tabla Técnica de Salud
    with st.expander("Ver Detalles Técnicos de Salud de Activos"):
        st.dataframe(df_pred, use_container_width=True, hide_index=True)

else:
    st.info("Sincronizando con los modelos de regresión... Los datos aparecerán cuando la telemetría esté activa.")