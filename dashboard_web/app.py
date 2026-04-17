import streamlit as st
import requests
import time

st.set_page_config(page_title="Planta Bellohorizonte V1.2", layout="wide")
API_URL = "http://api-servicio:8000"

st.title("🏭 Planta Industrial Bellohorizonte - Gestión Proactiva")

def fetch_data():
    try: return requests.get(f"{API_URL}/maquinas/estado-general").json()
    except: return []

data = fetch_data()

if data:
    # --- SECCIÓN DE KPIs ---
    total = len(data)
    apagadas = len([m for m in data if m['estado_actual'] == 'APAGADA'])
    criticas = len([m for m in data if m['decision_id'] == 2])
    riesgosas = len([m for m in data if m['decision_id'] == 1])
    
    disponibilidad = ((total - apagadas - criticas) / total) * 100
    perdida_min = ((apagadas + criticas) * 150) / 60

    st.subheader("📊 Indicadores Clave de Gestión (KPI)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("OEE (Disponibilidad)", f"{disponibilidad:.1f}%")
    k2.metric("Pérdida Financiera", f"${perdida_min:.2f} USD/min", delta_color="inverse")
    k3.metric("Alertas Críticas", criticas)
    k4.metric("En Riesgo", riesgosas)

    st.divider()

    # --- GRILLA DE EQUIPOS ---
    grid = st.columns(5)
    for i, maq in enumerate(data):
        with grid[i % 5]:
            color = "gray" if maq['decision_id'] == -1 else "green" if maq['decision_id'] == 0 else "orange" if maq['decision_id'] == 1 else "red"
            temp = f"{maq['valor_promedio']:.1f}°C" if maq['valor_promedio'] else "--"
            st.markdown(f"""
                <div style="border: 2px solid {color}; padding: 10px; border-radius: 8px; text-align: center;">
                    <h4 style="margin:0;">{maq['id_maquina']}</h4>
                    <p style="color:{color}; font-weight:bold; margin:2px;">{temp}</p>
                </div>
            """, unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()