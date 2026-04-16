import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Consola de Ingeniería del Caos", page_icon="🌪️", layout="wide")

API_URL = "http://api-servicio:8000"

st.markdown("<h1 style='color: #EF553B;'>🌪️ Consola de Ingeniería del Caos</h1>", unsafe_allow_html=True)
st.write("Inyecta fallas y controla el estado de las máquinas en tiempo real.")

# --- FUNCIÓN PARA ENVIAR COMANDOS A LA API ---
def update_estado(maquina_id, nuevo_estado):
    try:
        # 1. Actualizar el estado en la DB
        res = requests.post(f"{API_URL}/logs/", json={
            "tipo_evento": "USUARIO_CAOS",
            "maquina_id": maquina_id,
            "descripcion": f"Cambio de estado manual a: {nuevo_estado}"
        })
        
        # 2. Nota: Aquí asumimos que la API también tiene un endpoint para cambiar el estado
        # Si no lo has creado, el Dashboard sigue conectándose directo a la DB para este paso rápido
        import psycopg2
        conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute("UPDATE estado_maquinas SET estado_actual = %s, ultima_modificacion = CURRENT_TIMESTAMP WHERE id_maquina = %s;", (nuevo_estado, maquina_id))
        conn.commit()
        conn.close()
        
        st.success(f"✅ Orden enviada: {maquina_id} -> {nuevo_estado}")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error al procesar el comando: {e}")

# --- INTERFAZ DE CONTROL ---
maquinas = [f"M-{str(i).zfill(3)}" for i in range(1, 21)]
maq_objetivo = st.selectbox("Seleccione la Máquina Objetivo:", maquinas)

col1, col2 = st.columns([1, 1])

with col1:
    with st.container(border=True):
        st.subheader("🛠️ Control Operativo")
        if st.button("🟢 Restaurar a NORMAL", use_container_width=True):
            update_estado(maq_objetivo, "NORMAL")
        if st.button("🛑 APAGAR MÁQUINA", type="primary", use_container_width=True):
            update_estado(maq_objetivo, "APAGADA")

with col2:
    with st.container(border=True):
        st.subheader("⚠️ Inyectar Anomalías")
        if st.button("🔥 Fricción Térmica", use_container_width=True):
            update_estado(maq_objetivo, "FRICCION_TERMICA")
        if st.button("📳 Desalineación Severa", use_container_width=True):
            update_estado(maq_objetivo, "DESALINEACION")
        if st.button("❄️ Falla de Refrigerante", use_container_width=True):
            update_estado(maq_objetivo, "FALLA_REFRIGERACION")

st.divider()

# --- NUEVA SECCIÓN: TABLA DE MONITOREO EN VIVO ---
st.subheader("📋 Estado Actual de la Planta (Vista de Consola)")

def fetch_status():
    try:
        response = requests.get(f"{API_URL}/maquinas/estado-general")
        return response.json()
    except:
        return []

data = fetch_status()

if data:
    df = pd.DataFrame(data)
    
    # Limpiamos el DataFrame para que sea legible en la tabla
    df_display = df[['id_maquina', 'estado_actual', 'valor_promedio', 'valor_maximo']].copy()
    df_display.columns = ['ID Máquina', 'Estado Configurado', 'Temp. Prom (°C)', 'Vibr. Máx (Hz)']
    
    # Aplicar estilos visuales a la tabla
    def color_estado(val):
        color = 'white'
        if val == 'NORMAL': color = '#d4edda'
        elif val == 'APAGADA': color = '#e2e3e5'
        else: color = '#f8d7da' # Fallas
        return f'background-color: {color}'

    st.table(df_display.style.applymap(color_estado, subset=['Estado Configurado']))
else:
    st.info("Esperando conexión con la API de estados...")

# Auto-refresh cada 10 segundos para ver los cambios reflejados
time.sleep(10)
st.rerun()