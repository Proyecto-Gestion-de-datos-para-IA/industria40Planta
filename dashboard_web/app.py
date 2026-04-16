import streamlit as st
import requests
import time

st.set_page_config(page_title="Planta Industrial Bellohorizonte", layout="wide")

API_URL = "http://api-servicio:8000"

st.title("🏭 Planta Industrial Bellohorizonte - Monitoreo IA")

def fetch_data():
    try:
        response = requests.get(f"{API_URL}/maquinas/estado-general")
        return response.json()
    except:
        return []

data = fetch_data()

if not data:
    st.error("No se pudo conectar con la API de datos. Verificando...")
else:
    # --- KPIs ---
    total = len(data)
    apagadas = len([m for m in data if m['estado_actual'] == 'APAGADA'])
    criticas = len([m for m in data if m['decision_id'] == 2])
    
    cols = st.columns(4)
    cols[0].metric("Total Máquinas", total)
    cols[1].metric("En Producción", total - apagadas)
    cols[2].metric("Alertas Críticas", criticas, delta_color="inverse")
    cols[3].metric("Estado General", "Óptimo" if criticas == 0 else "Riesgo")

    st.divider()

    # --- SIMBOLOGÍA ---
    st.markdown("""
    **Simbología de Estado IA:**
    🟢 **NORMAL:** Operación óptima | 🟠 **RIESGO:** Falla incipiente (Precaución) | 🔴 **FALLA:** Peligro de rotura (Acción inmediata) | ⚪ **INACTIVA:** Máquina Apagada
    """)
    st.write("")

    # --- GRILLA DE MÁQUINAS ---
    grid = st.columns(5)
    for i, maq in enumerate(data):
        with grid[i % 5]:
            color = "gray" if maq['decision_id'] == -1 else \
                    "green" if maq['decision_id'] == 0 else \
                    "orange" if maq['decision_id'] == 1 else "red"
            
            status_text = "INACTIVA" if maq['decision_id'] == -1 else \
                          "NORMAL" if maq['decision_id'] == 0 else \
                          "RIESGO" if maq['decision_id'] == 1 else "FALLA CRÍTICA"
            
            # Formatear valores (por si Spark aún no procesa la primera ventana)
            temp = f"{maq['valor_promedio']:.1f}°C" if maq['valor_promedio'] is not None else "-- °C"
            vib = f"{maq['valor_maximo']:.1f} Hz" if maq['valor_maximo'] is not None else "-- Hz"

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

st.empty()
time.sleep(2)
st.rerun()