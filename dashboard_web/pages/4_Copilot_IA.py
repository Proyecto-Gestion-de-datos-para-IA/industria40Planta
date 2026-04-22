import streamlit as st
import requests
from google import genai # NUEVA IMPORTACIÓN OFICIAL

st.set_page_config(page_title="Copilot IA", page_icon="🤖", layout="wide")

API_URL = "http://api-servicio:8000"

st.markdown("<h1 style='color: #4B8BBE;'>🤖 Copilot de Mantenimiento Industrial</h1>", unsafe_allow_html=True)
st.write("Asistente cognitivo conectado en tiempo real a la telemetría de la planta Bellohorizonte.")

# --- Configuración de la API (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Configuración del Motor IA")
    st.write("Para habilitar el cerebro del Copilot, necesitas una clave API de Google Gemini.")
    api_key = st.text_input("Ingresa tu API Key:", type="password")
    st.markdown("[Obtener API Key gratuita aquí](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.write("ℹ️ **¿Cómo funciona?** (RAG)")
    st.write("El Copilot inyecta automáticamente el estado de la base de datos en cada pregunta que haces para darte contexto en tiempo real.")

# --- Función RAG: Leer la Planta ---
def obtener_contexto_planta():
    try:
        response = requests.get(f"{API_URL}/maquinas/estado-general", timeout=3)
        data = response.json()
        contexto = "REPORTE DE LA PLANTA EN TIEMPO REAL:\n"
        anomalias = 0
        
        for maq in data:
            if maq['estado_actual'] not in ["NORMAL", "APAGADA"]:
                contexto += f"- MÁQUINA {maq['id_maquina']}: ESTADO {maq['estado_actual']} | Temp: {maq['valor_promedio']}°C | Vibración: {maq['valor_maximo']}Hz\n"
                anomalias += 1
                
        if anomalias == 0:
            contexto += "Todas las máquinas operan con normalidad. Ninguna alerta crítica."
            
        return contexto
    except Exception:
        return "Error interno: No se pudo conectar a la API de telemetría."

# --- Inicializar el Historial de Chat ---
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {"role": "assistant", "content": "Hola, soy tu Copilot de Mantenimiento. Estoy monitoreando la telemetría en vivo de la Planta Bellohorizonte. ¿En qué te puedo ayudar hoy?"}
    ]

for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Lógica de Interacción ---
if prompt := st.chat_input("Ej: ¿Cuál es el protocolo de emergencia para la falla de la M-001?"):
    
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        if not api_key:
            st.warning("⚠️ Ingresa tu API Key en el menú lateral para activar al asistente.")
        else:
            try:
                # NUEVA SINTAXIS DE CONEXIÓN (SDK Moderno)
                client = genai.Client(api_key=api_key)
                
                contexto_vivo = obtener_contexto_planta()
                prompt_enriquecido = f"""
                Eres un Ingeniero Jefe de Mantenimiento Industrial experto en la Industria 4.0.
                Tu tarea es asistir al operador de la planta. Sé técnico, estructurado y directo.
                Utiliza listas o pasos (1, 2, 3) si es un protocolo de reparación.
                
                {contexto_vivo}
                
                PREGUNTA DEL OPERADOR: {prompt}
                """
                
                with st.spinner("Analizando telemetría y redactando respuesta..."):
                    # Usando el modelo Gemini 2.0 Flash moderno
                    response = client.models.generate_content(
                        model='gemini-2.0-flash', 
                        contents=prompt_enriquecido
                    )
                    texto_ia = response.text
                    
                st.markdown(texto_ia)
                st.session_state.mensajes.append({"role": "assistant", "content": texto_ia})
                
            except Exception as e:
                st.error(f"Se perdió la conexión con el motor cognitivo: {e}")