import streamlit as st
import psycopg2
import pandas as pd

st.set_page_config(page_title="Consola del Caos", page_icon="🌪️", layout="wide")

def update_estado(maquina, nuevo_estado):
    try:
        conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute(
            "UPDATE estado_maquinas SET estado_actual = %s, ultima_modificacion = CURRENT_TIMESTAMP WHERE id_maquina = %s",
            (nuevo_estado, maquina)
        )
        conn.commit()
        conn.close()
        st.toast(f"Comando enviado: {maquina} -> {nuevo_estado}")
    except Exception as e:
        st.error(f"Error de BD: {e}")

st.markdown("<h1 style='color: #EF553B; text-align: center;'>🌪️ Ingeniería del Caos (Inyector de Fallas)</h1>", unsafe_allow_html=True)
st.markdown("Usa este panel para alterar físicamente el comportamiento de los motores en el simulador Kafka. La Inteligencia Artificial deberá detectar la anomalía en tiempo real.")
st.divider()

col_control, col_estado = st.columns([1, 1.5])

with col_control:
    st.subheader("🛠️ Panel de Inyección")
    lista_maquinas = [f"M-{str(i).zfill(3)}" for i in range(1, 21)]
    maq_objetivo = st.selectbox("Seleccionar Activo a sabotear:", lista_maquinas)
    
    st.markdown("#### Seleccionar Evento Físico:")
    if st.button("🟢 Restaurar a NORMAL", use_container_width=True):
        update_estado(maq_objetivo, "NORMAL")
    if st.button("🔥 Inyectar FRICCIÓN TÉRMICA (Sube Temp)", use_container_width=True):
        update_estado(maq_objetivo, "FRICCION_TERMICA")
    if st.button("📳 Inyectar DESALINEACIÓN (Sube Vib)", use_container_width=True):
        update_estado(maq_objetivo, "DESALINEACION")
    if st.button("❄️ Falla de Refrigerante (Calor Extremo)", use_container_width=True):
        update_estado(maq_objetivo, "FALLA_REFRIGERACION")
    if st.button("🔩 Soltura de Base (Vibración Extrema)", use_container_width=True):
        update_estado(maq_objetivo, "SOLTURA_BASE")
    if st.button("💥 Forzar FALLA CATASTRÓFICA", use_container_width=True):
        update_estado(maq_objetivo, "FALLA_CATASTROFICA")

with col_estado:
    st.subheader("📋 Estado Actual del Clúster")
    if st.button("🔄 Actualizar Tabla"):
        try:
            conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
            df_estados = pd.read_sql("SELECT * FROM estado_maquinas ORDER BY id_maquina;", conn)
            conn.close()
            # Destacamos visualmente las que no están normales
            def highlight_errors(val):
                color = 'red' if val != 'NORMAL' else 'green'
                return f'color: {color}'
            
            st.dataframe(df_estados.style.map(highlight_errors, subset=['estado_actual']), use_container_width=True, hide_index=True)
        except:
            st.warning("No se pudo cargar la tabla de estados.")