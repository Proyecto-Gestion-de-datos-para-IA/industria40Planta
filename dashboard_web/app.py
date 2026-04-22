import streamlit as st
import requests
import time

# 🚨 REGLA DE ORO: set_page_config DEBE SER EL PRIMER COMANDO 🚨
st.set_page_config(page_title="Planta Bellohorizonte V2.5", layout="wide")

# =============================================================================
# MÓDULO: Monitor en Vivo (Dashboard Principal)
# VERSIÓN: 2.5
# =============================================================================

API_URL = "http://api-servicio:8000"

st.title("🏭 Planta Industrial Bellohorizonte - Monitor en Vivo")

def fetch_data():
    try: 
        return requests.get(f"{API_URL}/maquinas/estado-general").json()
    except: 
        return []

data = fetch_data()

if not data:
    st.error("No se pudo conectar con la API de datos. Verificando...")
else:
    # --- 1. KPIs FINANCIEROS Y DE GESTIÓN ---
    total = len(data)
    apagadas = len([m for m in data if m['estado_actual'] == 'APAGADA'])
    criticas = len([m for m in data if m['decision_id'] == 2])
    riesgosas = len([m for m in data if m['decision_id'] == 1])
    operativas = total - apagadas - criticas
    
    disponibilidad = (operativas / total) * 100 if total > 0 else 0
    perdida_min = ((apagadas + criticas) * 150) / 60

    st.subheader("📈 Indicadores Clave de Desempeño (KPIs)")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("OEE (Disponibilidad)", f"{disponibilidad:.1f}%", f"{disponibilidad - 100:.1f}% vs Ideal")
    k2.metric("Pérdida Financiera", f"${perdida_min:.2f} USD/min", "Impacto por inactividad", delta_color="inverse")
    k3.metric("Alertas Críticas", criticas, "Requieren detención inmediata", delta_color="inverse" if criticas > 0 else "normal")
    k4.metric("Máquinas en Riesgo", riesgosas, "Requieren mantenimiento preventivo", delta_color="off")

    st.divider()

    # --- 2. SIMBOLOGÍA ---
    st.markdown("**Simbología de Estado IA:** 🟢 **NORMAL** | 🟠 **RIESGO** | 🔴 **FALLA** | ⚪ **INACTIVA**")
    st.write("")

    # --- 3. GRILLA DE EQUIPOS (Tarjetas Completas) ---
    grid = st.columns(5)
    for i, maq in enumerate(data):
        with grid[i % 5]:
            color = "gray" if maq['decision_id'] == -1 else \
                    "green" if maq['decision_id'] == 0 else \
                    "orange" if maq['decision_id'] == 1 else "red"
            
            status_text = "INACTIVA" if maq['decision_id'] == -1 else \
                          "NORMAL" if maq['decision_id'] == 0 else \
                          "RIESGO" if maq['decision_id'] == 1 else "FALLA CRÍTICA"
            
            temp = f"{maq['valor_promedio']:.1f}°C" if maq['valor_promedio'] else "-- °C"
            vib = f"{maq['valor_maximo']:.1f} Hz" if maq['valor_maximo'] else "-- Hz"

            st.markdown(f"""
                <div style="border: 2px solid {color}; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;">
                    <h3 style="margin-bottom: 0px;">{maq['id_maquina']}</h3>
                    <p style="color: {color}; font-weight: bold; margin-top: 5px; font-size: 14px;">{status_text}</p>
                    <div style="font-size: 13px; color: #666;">
                        🌡️ Temp: <b>{temp}</b><br>
                        📳 Vibr: <b>{vib}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# Refresco automático
st.empty()
time.sleep(5)
st.rerun()