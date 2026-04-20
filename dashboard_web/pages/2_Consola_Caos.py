import streamlit as st
import requests
import psycopg2
import time
import pandas as pd

st.set_page_config(page_title="Consola de Ingeniería del Caos", page_icon="🌪️", layout="wide")

API_URL = "http://api-servicio:8000"

st.markdown("<h1 style='color: #EF553B;'>🌪️ Consola de Ingeniería del Caos</h1>", unsafe_allow_html=True)
st.write("Inyecta fallas progresivas y controla el estado de las máquinas en tiempo real.")

def update_estado(maquina_id, nuevo_estado):
    try:
        requests.post(f"{API_URL}/logs/", json={
            "tipo_evento": "USUARIO_CAOS",
            "maquina_id": maquina_id,
            "descripcion": f"Cambio manual de estado a: {nuevo_estado}"
        })
        
        conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute("UPDATE estado_maquinas SET estado_actual = %s, ultima_modificacion = CURRENT_TIMESTAMP WHERE id_maquina = %s;", (nuevo_estado, maquina_id))
        conn.commit()
        conn.close()
        st.success(f"✅ Orden enviada: {maquina_id} -> {nuevo_estado}")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error conectando a la BD o API: {e}")

maquinas = [f"M-{str(i).zfill(3)}" for i in range(1, 21)]
maq_objetivo = st.selectbox("Seleccione la Máquina Objetivo:", maquinas)

# --- BOTONES DE CAOS ALINEADOS AL SIMULADOR ---
col_op, col_riesgo, col_crit = st.columns(3)

with col_op:
    with st.container(border=True):
        st.subheader("🛠️ Operación")
        if st.button("🟢 Restaurar a NORMAL", use_container_width=True): update_estado(maq_objetivo, "NORMAL")
        st.write("")
        if st.button("🛑 APAGAR MÁQUINA", type="primary", use_container_width=True): update_estado(maq_objetivo, "APAGADA")

with col_riesgo:
    with st.container(border=True):
        st.subheader("⚠️ Anomalías (Riesgosas)")
        if st.button("🟠 Fricción Leve", use_container_width=True): update_estado(maq_objetivo, "FRICCION_LEVE")
        if st.button("🟠 Desalineación Leve", use_container_width=True): update_estado(maq_objetivo, "DESALINEACION_LEVE")
        if st.button("🟠 Falta de Lubricación", use_container_width=True): update_estado(maq_objetivo, "FALTA_LUBRICACION")
        if st.button("🟠 Desgaste Rodamiento", use_container_width=True): update_estado(maq_objetivo, "DESGASTE_RODAMIENTO")
        if st.button("🟠 Sobrecarga Ligera", use_container_width=True): update_estado(maq_objetivo, "SOBRECARGA_LIGERA")

with col_crit:
    with st.container(border=True):
        st.subheader("🚨 Fallas (Críticas)")
        if st.button("🔴 Fricción Severa", use_container_width=True): update_estado(maq_objetivo, "FRICCION_SEVERA")
        if st.button("🔴 Desalineación Severa", use_container_width=True): update_estado(maq_objetivo, "DESALINEACION_SEVERA")
        if st.button("🔴 Falla Refrigeración", use_container_width=True): update_estado(maq_objetivo, "FALLA_REFRIGERACION")
        if st.button("🔴 Soltura de Base", use_container_width=True): update_estado(maq_objetivo, "SOLTURA_BASE")
        if st.button("🔴 Rotura de Engranaje", use_container_width=True): update_estado(maq_objetivo, "ROTURA_ENGRANAJE")

st.divider()

# --- TABLA DE MONITOREO ---
st.subheader("📋 Estado Actual de la Planta")

def fetch_status():
    try: return requests.get(f"{API_URL}/maquinas/estado-general").json()
    except: return []

data = fetch_status()

if data:
    df = pd.DataFrame(data)
    df_display = df[['id_maquina', 'estado_actual', 'valor_promedio', 'valor_maximo']].copy()
    df_display.columns = ['ID Máquina', 'Estado Configurado', 'Temp. Prom (°C)', 'Vibr. Máx (Hz)']
    
    def color_estado(val):
        if val == 'NORMAL': return 'background-color: #d4edda'
        elif val == 'APAGADA': return 'background-color: #e2e3e5'
        elif any(c in str(val) for c in ['SEVERA', 'FALLA', 'SOLTURA', 'ROTURA']): return 'background-color: #f8d7da'
        else: return 'background-color: #fff3cd'

    st.table(df_display.style.applymap(color_estado, subset=['Estado Configurado']))
else:
    st.info("Esperando conexión con la API...")

time.sleep(10)
st.rerun()