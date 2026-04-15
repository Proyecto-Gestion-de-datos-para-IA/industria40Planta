import streamlit as st
import psycopg2

st.set_page_config(page_title="Consola de Ingeniería del Caos", page_icon="🌪️")

st.markdown("<h1 style='color: #EF553B;'>🌪️ Consola de Ingeniería del Caos</h1>", unsafe_allow_html=True)
st.write("Inyecta fallas mecánicas y térmicas en el Gemelo Digital para probar la respuesta de la Inteligencia Artificial.")

def update_estado(maquina_id, nuevo_estado):
    try:
        conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute("UPDATE estado_maquinas SET estado = %s WHERE id_sensor = %s;", (nuevo_estado, maquina_id))
        conn.commit()
        conn.close()
        st.success(f"[{maquina_id}] Estado actualizado a: {nuevo_estado}")
    except Exception as e:
        st.error(f"Error de conexión a la BD: {e}")

maq_objetivo = st.selectbox("Seleccione la Máquina Objetivo:", [f"M-{str(i).zfill(3)}" for i in range(1, 21)])

with st.container(border=True):
    st.subheader(f"Inyectar Anomalías en {maq_objetivo}")
    
    if st.button("🟢 Restaurar a NORMAL", use_container_width=True):
        update_estado(maq_objetivo, "NORMAL")
    if st.button("🔥 Fricción Térmica", use_container_width=True):
        update_estado(maq_objetivo, "FRICCION_TERMICA")
    if st.button("📳 Desalineación Severa", use_container_width=True):
        update_estado(maq_objetivo, "DESALINEACION")
    
    st.markdown("#### Fallas Críticas:")
    if st.button("❄️ Falla de Refrigerante (Calor Extremo)", use_container_width=True):
        update_estado(maq_objetivo, "FALLA_REFRIGERACION")
    if st.button("🔩 Soltura de Base (Vibración Extrema)", use_container_width=True):
        update_estado(maq_objetivo, "SOLTURA_BASE")
        
    st.divider()
    st.markdown("#### 🚨 Control de Emergencia")
    if st.button("🛑 APAGAR MÁQUINA INMEDIATAMENTE", type="primary", use_container_width=True):
        update_estado(maq_objetivo, "APAGADA")
        st.toast(f"Orden de PARADA DE EMERGENCIA enviada a {maq_objetivo}")