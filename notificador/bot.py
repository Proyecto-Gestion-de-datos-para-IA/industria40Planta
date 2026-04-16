import requests
import time
import os

# Obtiene las variables desde Docker Compose
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
API_URL = "http://api-servicio:8000"

alertas_activas = set()

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})
        if response.status_code == 200:
            print("✅ Telegram enviado con éxito!")
        else:
            print(f"⚠️ Telegram rechazó el mensaje. Razón: {response.text}")
    except Exception as e:
        print(f"❌ Error de red hacia Telegram: {e}")

def registrar_log_api(maquina, descripcion):
    try:
        requests.post(f"{API_URL}/logs/", json={
            "tipo_evento": "NOTIFICACION",
            "maquina_id": maquina,
            "descripcion": descripcion
        })
    except:
        pass

print("🤖 Notificador de Telegram Iniciado. Monitoreando planta...")

while True:
    try:
        # 1. Consultar estado general
        res = requests.get(f"{API_URL}/maquinas/estado-general")
        maquinas = res.json()
        
        for m in maquinas:
            id_maq = m['id_maquina']
            decision = m['decision_id']
            
            # 2. Si hay falla crítica y no hemos avisado
            if decision == 2 and id_maq not in alertas_activas:
                mensaje = f"🚨 EMERGENCIA EN PLANTA 🚨\nMáquina: {id_maq}\nProblema: Posible falla mecánica/térmica inminente.\nAcción: Requiere parada y revisión."
                enviar_telegram(mensaje)
                registrar_log_api(id_maq, "Alerta enviada al Jefe de Planta vía Telegram.")
                alertas_activas.add(id_maq)
            
            # 3. Si la máquina volvió a la normalidad (o fue reparada)
            elif decision <= 0 and id_maq in alertas_activas:
                mensaje = f"✅ Máquina {id_maq} estabilizada y operando normalmente."
                enviar_telegram(mensaje)
                registrar_log_api(id_maq, "Resolución de alerta notificada vía Telegram.")
                alertas_activas.remove(id_maq)
                
    except requests.exceptions.ConnectionError:
        print("⏳ Esperando que la API termine de arrancar...")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    time.sleep(15) # Revisar cada 15 segundos