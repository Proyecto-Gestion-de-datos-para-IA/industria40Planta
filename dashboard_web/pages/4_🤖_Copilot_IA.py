import streamlit as st
import requests
from google import genai # Utilizando el SDK oficial de última generación

#"""
#=============================================================================
#MÓDULO: Copilot de Mantenimiento Predictivo (Capa Cognitiva LLM)
#ARCHIVO: pages/4_🤖_Copilot_IA.py
#VERSIÓN: 2.5
#=============================================================================
#DESCRIPCIÓN:
#Interfaz de lenguaje natural que actúa como orquestador de información. 
#Utiliza un modelo de lenguaje masivo (Gemini 2.0 Flash) para razonar sobre 
#los datos técnicos de la planta.

#ARQUITECTURA IA (RAG - Retrieval Augmented Generation):
#1. Recuperación: Extrae el estado actual de las 20 máquinas desde la API.
#2. Aumentación: Inyecta esos datos en un 'System Prompt' estructurado.
#3. Generación: Envía el contexto + la duda del usuario al modelo para 
#   obtener una respuesta fundamentada en datos reales (Grounding).

#MODELO: Gemini 2.0 Flash (Baja latencia, alta ventana de contexto).
#=============================================================================
#"""

st.set_page_config(page_title="Copilot IA V2.5", page_icon="🤖", layout="wide")
API_URL = "http://api-servicio:8000"

st.markdown("<h1 style='color: #4B8BBE;'>🤖 Copilot de Mantenimiento v2.5</h1>", unsafe_allow_html=True)
st.write("Asistente experto con acceso en tiempo real a la telemetría y diagnósticos de la planta.")

# =============================================================================
# 1. CONFIGURACIÓN DE SEGURIDAD Y MOTOR IA
# =============================================================================
with st.sidebar:
    st.header("⚙️ Configuración del Motor")
    st.write("El Copilot utiliza **Gemini 2.0 Flash** para razonar sobre anomalías.")
    api_key = st.text_input("Google API Key:", type="password", help="Tu llave nunca se guarda en el servidor, solo reside en la sesión de tu navegador.")
    st.markdown("[Obtener API Key gratuita](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.caption("🤖 **Arquitectura RAG activa**: Cada consulta es enriquecida con el estado de los 20 activos de la planta.")

# =============================================================================
# 2. CAPA DE CONTEXTO (GROUNDING)
# =============================================================================
def obtener_contexto_planta():
    """
    Función de 'Retrieval': Transforma la base de datos relacional en 
    lenguaje natural comprensible para el modelo de lenguaje.
    """
    try:
        response = requests.get(f"{API_URL}/maquinas/estado-general", timeout=3)
        data = response.json()
        contexto = "--- ESTADO ACTUAL DE LA PLANTA (SNAPSHOT) ---\n"
        anomalias = 0
        
        for maq in data:
            # Solo inyectamos detalles de máquinas que no están normales para ahorrar tokens
            if maq['estado_actual'] not in ["NORMAL", "APAGADA"]:
                contexto += (f"- ACTIVO {maq['id_maquina']}: "
                           f"Alerta de {maq['estado_actual']} | "
                           f"Temp: {maq['valor_promedio']}°C | "
                           f"Vib: {maq['valor_maximo']}Hz\n")
                anomalias += 1
                
        if anomalias == 0:
            contexto += "Estado Operativo: Óptimo. Sin desviaciones detectadas en telemetría."
            
        return contexto
    except:
        return "Aviso: No se pudo recuperar la telemetría en vivo. Responde basado en conocimientos generales de ingeniería."

# =============================================================================
# 3. INTERFAZ DE CHAT (EXPERIENCIA DE USUARIO)
# =============================================================================
if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        {"role": "assistant", "content": "Hola Sebastián, soy tu Copilot. Tengo acceso a los sensores y cámaras térmicas. ¿Hay algún equipo que te preocupe?"}
    ]

# Renderizado del historial
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada de usuario
if prompt := st.chat_input("Ej: ¿Qué máquinas presentan riesgo de sobrecalentamiento?"):
    
    st.session_state.mensajes.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        if not api_key:
            st.warning("⚠️ El cerebro del Copilot está desconectado. Ingresa tu API Key en el menú lateral.")
        else:
            try:
                # Inicialización del cliente con el nuevo SDK de Google
                client = genai.Client(api_key=api_key)
                
                # Proceso de Aumentación (Enriquecimiento del Prompt)
                contexto_vivo = obtener_contexto_planta()
                
                # Definición de la Personalidad y Reglas (System Instruction)
                prompt_maestro = f"""
                CONTEXTO PROFESIONAL:
                Eres un Ingeniero Senior de Confiabilidad con 20 años de experiencia. 
                Tu tono es profesional, analítico y preventivo. 
                Utiliza terminología técnica (lucro cesante, MTBF, degradación, etc.).

                DATOS EN TIEMPO REAL DE LA PLANTA:
                {contexto_vivo}

                INSTRUCCIÓN:
                Responde a la duda del operador basándote PRIMERO en los datos de arriba. 
                Si hay una falla, sugiere protocolos de seguridad inmediatos.
                
                DUDA DEL OPERADOR: {prompt}
                """
                
                with st.spinner("Consultando telemetría..."):
                    # Generación usando el modelo Flash (Equilibrio perfecto velocidad/costo)
                    response = client.models.generate_content(
                        model='gemini-2.0-flash', 
                        contents=prompt_maestro
                    )
                    texto_ia = response.text
                    
                    st.markdown(texto_ia)
                    st.session_state.mensajes.append({"role": "assistant", "content": texto_ia})
                
            except Exception as e:
                st.error(f"Error en el motor cognitivo: {e}")