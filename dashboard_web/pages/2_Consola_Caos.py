import streamlit as st
import requests
import psycopg2
import time

st.title("🌪️ Consola de Ingeniería del Caos")
API_URL = "http://api-servicio:8000"

maq_id = st.selectbox("Objetivo:", [f"M-{str(i).zfill(3)}" for i in range(1, 21)])

def enviar_caos(estado):
    try:
        # 1. Registrar Log
        requests.post(f"{API_URL}/logs/", json={"tipo_evento":"CAOS","maquina_id":maq_id,"descripcion":f"Inyectado: {estado}"})
        # 2. Update DB
        conn = psycopg2.connect(host="iot-postgres", database="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute("UPDATE estado_maquinas SET estado_actual = %s WHERE id_maquina = %s", (estado, maq_id))
        conn.commit()
        conn.close()
        st.success(f"Estado {estado} aplicado.")
    except Exception as e: st.error(e)

c1, c2, c3 = st.columns(3)
with c1: 
    if st.button("🟢 NORMAL"): enviar_caos("NORMAL")
    if st.button("🛑 APAGAR"): enviar_caos("APAGADA")
with c2:
    st.write("⚠️ RIESGOS")
    if st.button("🟠 Fricción Leve"): enviar_caos("FRICCION_LEVE")
    if st.button("🟠 Desgaste"): enviar_caos("DESGASTE_RODAMIENTO")
with c3:
    st.write("🚨 CRÍTICOS")
    if st.button("🔴 Falla Refrig."): enviar_caos("FALLA_REFRIGERACION")
    if st.button("🔴 Soltura Base"): enviar_caos("SOLTURA_BASE")