import streamlit as st
import numpy as np
import plotly.express as px
import json
import time
from kafka import KafkaConsumer
import tensorflow as tf

st.set_page_config(page_title="CCTV Térmico IA", page_icon="🎥", layout="wide")

# Cargar el modelo CNN (Se guarda en caché para optimizar rendimiento)
@st.cache_resource
def cargar_cerebro_visual():
    return tf.keras.models.load_model("modelo_vision_termica.h5")

try:
    modelo_cnn = cargar_cerebro_visual()
except Exception as e:
    st.error(f"Error cargando el modelo CNN: {e}. Asegúrate de que modelo_vision_termica.h5 está en la carpeta dashboard.")
    st.stop()

st.markdown("<h1 style='color: #4B8BBE;'>🎥 Central de Monitoreo CCTV - Visión IA</h1>", unsafe_allow_html=True)
st.write("Análisis termográfico en tiempo real potenciado por Redes Neuronales Convolucionales (CNN) de 4 Clases.")

# Selector de Cámara
maq_objetivo = st.selectbox("Seleccionar alimentación de cámara:", [f"M-{str(i).zfill(3)}" for i in range(1, 21)])
st.divider()

col_video, col_ia = st.columns([2, 1])

# Configurar el consumidor de Kafka
def obtener_ultimo_frame(maquina_id):
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
    except Exception as e:
        return None

# Bucle de Streaming en UI
frame_crudo = obtener_ultimo_frame(maq_objetivo)

with col_video:
    st.subheader(f"🔴 REC: Cámara Térmica {maq_objetivo}")
    if frame_crudo:
        matriz = np.array(frame_crudo)
        fig = px.imshow(matriz, color_continuous_scale='inferno', origin='lower', range_color=[0, 1])
        fig.update_layout(coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Buscando señal de video en el tópico de Kafka...")

with col_ia:
    st.subheader("🧠 Diagnóstico CNN")
    if frame_crudo:
        tensor_img = np.array(frame_crudo).reshape(1, 64, 64, 1)
        
        # Inferencia
        predicciones = modelo_cnn.predict(tensor_img, verbose=0)[0]
        clase_predicha = np.argmax(predicciones)
        confianza = np.max(predicciones) * 100
        
        # DICCIONARIO V2.0 CON 4 CLASES
        clases = {
            0: ("NORMAL", "green"), 
            1: ("FRICCIÓN EN EJE", "red"), 
            2: ("ANOMALÍA EN SOPORTES", "orange"),
            3: ("COLAPSO REFRIGERANTE", "purple")
        }
        diagnostico, color = clases.get(clase_predicha, ("DESCONOCIDO", "gray"))
        
        st.markdown(f"""
            <div style="border: 2px solid {color}; padding: 20px; border-radius: 10px; text-align: center;">
                <h4 style="margin-bottom: 0;">Análisis Visual:</h4>
                <h2 style="color: {color}; margin-top: 10px;">{diagnostico}</h2>
                <p>Nivel de Confianza IA: <b>{confianza:.2f}%</b></p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.write("**Probabilidades en bruto:**")
        
        # BARRAS DE PROGRESO DINÁMICAS (Para evitar errores si el modelo viejo sigue cargado)
        if len(predicciones) >= 3:
            st.progress(float(predicciones[0]), text=f"Normal: {predicciones[0]*100:.1f}%")
            st.progress(float(predicciones[1]), text=f"Fricción: {predicciones[1]*100:.1f}%")
            st.progress(float(predicciones[2]), text=f"Soportes: {predicciones[2]*100:.1f}%")
        if len(predicciones) == 4:
            st.progress(float(predicciones[3]), text=f"Colapso Ref.: {predicciones[3]*100:.1f}%")
        elif len(predicciones) < 4:
            st.error("⚠️ El modelo cargado en RAM es la V1 (3 Clases). Reinicia el contenedor.")

time.sleep(2)
st.rerun()