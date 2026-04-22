import streamlit as st
import numpy as np
import plotly.express as px
import json
import time
from kafka import KafkaConsumer
import tensorflow as tf

#"""
#=============================================================================
#MÓDULO: Central de Visión Artificial y Termografía (CNN)
#ARCHIVO: pages/3_🌡️_CCTV_Termico.py
#VERSIÓN: 2.5
#=============================================================================
#DESCRIPCIÓN:
#Sistema de monitoreo visual basado en Deep Learning. Procesa flujos de video 
#no estructurados provenientes de cámaras térmicas simuladas.

#ARQUITECTURA DE IA:
#1. Ingesta: Captura matrices de intensidades térmicas desde Kafka.
#2. Pre-procesamiento: Redimensiona y normaliza la matriz a un Tensor (1, 64, 64, 1).
#3. Inferencia: Ejecuta un modelo CNN de 4 clases para detectar patrones 
#   visuales de falla que los sensores numéricos podrían ignorar.

#CLASES DE DETECTADAS (V2.5):
#- 0: NORMAL (Distribución de calor uniforme)
#- 1: FRICCIÓN (Hotspot localizado en eje)
#- 2: ANOMALÍA SOPORTES (Calor en base/pernos)
#- 3: COLAPSO REFRIGERANTE (Elevación térmica global)
#=============================================================================
#"""

st.set_page_config(page_title="CCTV Térmico V2.5", page_icon="🎥", layout="wide")
API_URL = "http://api-servicio:8000"

# =============================================================================
# 1. CARGA DE RECURSOS (DEEP LEARNING ENGINE)
# =============================================================================
@st.cache_resource
def cargar_cerebro_visual():
    """
    Carga el modelo h5 en memoria. Se usa cache_resource para evitar 
    recargar los pesos del modelo en cada refresco de pantalla.
    """
    return tf.keras.models.load_model("modelo_vision_termica.h5")

try:
    modelo_cnn = cargar_cerebro_visual()
except Exception as e:
    st.error(f"🚨 Error crítico: No se encontró el cerebro visual (modelo_vision_termica.h5).")
    st.stop()

st.markdown("<h1 style='color: #4B8BBE;'>🎥 Monitoreo CCTV - Visión Artificial v2.5</h1>", unsafe_allow_html=True)
st.write("Análisis termográfico en tiempo real mediante Redes Neuronales Convolucionales (CNN).")

# Selector de Canal de Video
maq_objetivo = st.selectbox("Seleccionar alimentación de cámara:", [f"M-{str(i).zfill(3)}" for i in range(1, 21)])
st.divider()

col_video, col_ia = st.columns([2, 1])

# =============================================================================
# 2. CAPA DE INGESTA (KAFKA CONSUMER)
# =============================================================================
def obtener_ultimo_frame(maquina_id):
    """
    Se conecta al tópico de video para extraer el último frame generado.
    """
    try:
        consumer = KafkaConsumer(
            'video_termico',
            bootstrap_servers='kafka:9092',
            auto_offset_reset='latest',
            enable_auto_commit=False,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=1000 
        )
        
        ultimo_frame = None
        for mensaje in consumer:
            if mensaje.value['id_maquina'] == maquina_id:
                ultimo_frame = mensaje.value['frame_matriz']
        consumer.close()
        return ultimo_frame
    except:
        return None

# Obtención del dato crudo
frame_crudo = obtener_ultimo_frame(maq_objetivo)

# =============================================================================
# 3. CAPA DE VISUALIZACIÓN Y DIAGNÓSTICO
# =============================================================================
with col_video:
    st.subheader(f"🔴 FEED EN VIVO: {maq_objetivo}")
    if frame_crudo:
        # Transformamos la lista JSON en una matriz NumPy para procesamiento visual
        matriz = np.array(frame_crudo)
        
        # Renderizado térmico con escala 'inferno' (estándar industrial)
        fig = px.imshow(matriz, color_continuous_scale='inferno', origin='lower', range_color=[0, 1])
        fig.update_layout(coloraxis_showscale=True, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📡 Buscando señal... Asegúrese de que el simulador de cámara esté transmitiendo.")

with col_ia:
    st.subheader("🧠 Diagnóstico CNN")
    if frame_crudo:
        # PRE-PROCESAMIENTO: El modelo espera un tensor de 4 dimensiones (Batch, Alto, Ancho, Canales)
        tensor_img = np.array(frame_crudo).reshape(1, 64, 64, 1)
        
        # INFERENCIA: El modelo evalúa el patrón de píxeles
        predicciones = modelo_cnn.predict(tensor_img, verbose=0)[0]
        clase_predicha = np.argmax(predicciones)
        confianza = np.max(predicciones) * 100
        
        # Diccionario de Clases v2.5
        clases = {
            0: ("OPERACIÓN NORMAL", "green"), 
            1: ("FRICCIÓN EN EJE", "red"), 
            2: ("ANOMALÍA EN SOPORTES", "orange"),
            3: ("COLAPSO REFRIGERANTE", "purple")
        }
        diagnostico, color = clases.get(clase_predicha, ("INDETERMINADO", "gray"))
        
        # UI de Diagnóstico
        st.markdown(f"""
            <div style="border: 2px solid {color}; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="margin-bottom: 0;">Clasificación Visual:</h4>
                <h2 style="color: {color}; margin-top: 10px;">{diagnostico}</h2>
                <p>Nivel de Confianza: <b>{confianza:.2f}%</b></p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.write("**Desglose de Probabilidades:**")
        
        # Barras de probabilidad para monitorear la "incertidumbre" de la IA
        if len(predicciones) >= 3:
            st.progress(float(predicciones[0]), text=f"Normal: {predicciones[0]*100:.1f}%")
            st.progress(float(predicciones[1]), text=f"Fricción: {predicciones[1]*100:.1f}%")
            st.progress(float(predicciones[2]), text=f"Soportes: {predicciones[2]*100:.1f}%")
        if len(predicciones) == 4:
            st.progress(float(predicciones[3]), text=f"Colapso Ref.: {predicciones[3]*100:.1f}%")
        elif len(predicciones) < 4:
            st.warning("⚠️ Detectada discrepancia de versión en el modelo CNN.")

# Control de refresco de pantalla (2 segundos para no saturar la GPU/CPU)
time.sleep(2)
st.rerun()