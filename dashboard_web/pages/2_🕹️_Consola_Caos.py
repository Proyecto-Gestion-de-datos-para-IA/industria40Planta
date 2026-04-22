import streamlit as st
import requests
import psycopg2
import time
import pandas as pd

#"""
#=============================================================================
#MÓDULO: Consola de Ingeniería del Caos (Inyección de Eventos)
#ARCHIVO: pages/2_🕹️_Consola_del_Caos.py
#VERSIÓN: 2.5
#=============================================================================
#DESCRIPCIÓN:
#Interfaz de control para el Gemelo Digital. Permite manipular el estado 
#interno de las máquinas para simular escenarios de estrés y fallas.

#ARQUITECTURA DE CONTROL:
#1. Capa de Registro (API): Notifica cada intervención al microservicio de logs.
#2. Capa de Estado (Postgres): Modifica directamente la tabla 'estado_maquinas'.
#   El simulador IoT lee este cambio y ajusta su salida numérica de inmediato.

#RELEVANCIA PARA LA IA:
#Este módulo actúa como el 'Oracle' del sistema. Al inyectar fallas manuales, 
#proporcionamos los datos etiquetados necesarios para validar la precisión 
#del modelo Random Forest en Spark y entrenar futuros modelos de Clasificación.
#=============================================================================
#"""

st.set_page_config(page_title="Consola del Caos V2.5", page_icon="🌪️", layout="wide")
API_URL = "http://api-servicio:8000"

st.markdown("<h1 style='color: #EF553B;'>🌪️ Consola de Ingeniería del Caos v2.5</h1>", unsafe_allow_html=True)
st.write("Control maestro para la inyección de anomalías y validación de modelos predictivos.")

def update_estado(maquina_id, nuevo_estado):
    """
    Sincroniza el cambio de estado en la base de datos operacional y registra el evento.
    Es el gatillo que altera el comportamiento del simulador físico.
    """
    try:
        # Registro en el log de auditoría para trazabilidad de IA
        requests.post(f"{API_URL}/logs/", json={
            "tipo_evento": "USUARIO_CAOS",
            "maquina_id": maquina_id,
            "descripcion": f"Cambio manual de estado a: {nuevo_estado}"
        }, timeout=2)
        
        # Conexión directa a la BD para actualización de estado en tiempo real
        conn = psycopg2.connect(
            host="iot-postgres", 
            port="5432", 
            dbname="industria40", 
            user="admin", 
            password="admin123"
        )
        cur = conn.cursor()
        cur.execute("""
            UPDATE estado_maquinas 
            SET estado_actual = %s, ultima_modificacion = CURRENT_TIMESTAMP 
            WHERE id_maquina = %s;
        """, (nuevo_estado, maquina_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        st.success(f"✅ Orden de {nuevo_estado} enviada con éxito a {maquina_id}")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error de comunicación con la infraestructura: {e}")

# --- SELECCIÓN DE OBJETIVO ---
maquinas = [f"M-{str(i).zfill(3)}" for i in range(1, 21)]
maq_objetivo = st.selectbox(
    "Seleccione el activo para inyección de evento:", 
    maquinas,
    help="El cambio afectará inmediatamente los datos generados por el simulador de esta máquina."
)

st.divider()

# --- PANEL DE CONTROL DE FALLAS ---
col_op, col_riesgo, col_crit = st.columns(3)

with col_op:
    with st.container(border=True):
        st.subheader("🛠️ Gestión Operativa")
        if st.button("🟢 Restaurar a NORMAL", use_container_width=True, help="Limpia todas las anomalías inyectadas."): 
            update_estado(maq_objetivo, "NORMAL")
        st.write("")
        if st.button("🛑 PARADA DE EMERGENCIA", type="primary", use_container_width=True, help="Simula una máquina fuera de servicio."): 
            update_estado(maq_objetivo, "APAGADA")

with col_riesgo:
    with st.container(border=True):
        st.subheader("⚠️ Anomalías Leves")
        st.caption("Eventos que la IA debería clasificar como RIESGO (Decision ID = 1)")
        opts = ["FRICCION_LEVE", "DESALINEACION_LEVE", "FALTA_LUBRICACION", "DESGASTE_RODAMIENTO", "SOBRECARGA_LIGERA"]
        for opt in opts:
            if st.button(f"🟠 {opt.replace('_', ' ')}", use_container_width=True):
                update_estado(maq_objetivo, opt)

with col_crit:
    with st.container(border=True):
        st.subheader("🚨 Fallas Críticas")
        st.caption("Eventos que la IA debería clasificar como FALLA (Decision ID = 2)")
        opts_crit = ["FRICCION_SEVERA", "DESALINEACION_SEVERA", "FALLA_REFRIGERACION", "SOLTURA_BASE", "ROTURA_ENGRANAJE"]
        for opt in opts_crit:
            if st.button(f"🔴 {opt.replace('_', ' ')}", use_container_width=True):
                update_estado(maq_objetivo, opt)

st.divider()

# --- MONITOREO DE RESPUESTA ---
st.subheader("📋 Estado de Configuración de la Planta")

def fetch_status():
    """Consulta el estado configurado actualmente para todas las máquinas."""
    try: 
        res = requests.get(f"{API_URL}/maquinas/estado-general", timeout=3)
        return res.json()
    except: 
        return []

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
    st.caption("Esta tabla refleja el estado inyectado, no necesariamente la lectura actual del sensor.")
else:
    st.info("Sincronizando con el servidor de estados...")

# Refresco lento (10s) para no saturar la BD mientras el usuario decide qué falla inyectar
time.sleep(10)
st.rerun()