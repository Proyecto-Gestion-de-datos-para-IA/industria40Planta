import json
import time
import numpy as np
from datetime import datetime
from kafka import KafkaProducer
import psycopg2

"""
=============================================================================
MÓDULO: Productor de Telemetría IoT (Sensores Numéricos)
VERSIÓN: 2.5
DESCRIPCIÓN: 
Este script simula sensores físicos de la planta. Genera datos estructurados 
(Temperatura, Presión, Vibración) y los inyecta en un bus de mensajería (Kafka).
CONTEXTO DE INTELIGENCIA ARTIFICIAL:
Los datos generados aquí sirven como "Features" (características) de entrada 
para modelos de Machine Learning clásico. 
Actualmente preparados para: Detección de Anomalías (Ej. Isolation Forest).
Futuro: Predicción de Vida Útil Restante (RUL) mediante series temporales.
=============================================================================
"""

def obtener_configuracion_viva():
    try:
        conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute("SELECT id_maquina, estado_actual FROM estado_maquinas;")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return []

def generar_lectura(maquina_id, estado):
    # --- ESTADOS BASE ---
    if estado == "NORMAL":
        t, v = np.random.normal(40, 2), np.random.normal(10, 1)
    elif estado == "APAGADA":
        t, v = np.random.normal(22, 0.5), np.random.normal(0, 0.1)
        
    # --- 5 ESTADOS DE RIESGO ---
    elif estado == "FRICCION_LEVE":
        t, v = np.random.normal(65, 3), np.random.normal(15, 2)
    elif estado == "DESALINEACION_LEVE":
        t, v = np.random.normal(45, 2), np.random.normal(22, 2)
    elif estado == "FALTA_LUBRICACION":
        t, v = np.random.normal(70, 4), np.random.normal(18, 2)
    elif estado == "DESGASTE_RODAMIENTO":
        t, v = np.random.normal(50, 2), np.random.normal(25, 3)
    elif estado == "SOBRECARGA_LIGERA":
        t, v = np.random.normal(75, 3), np.random.normal(12, 1)

    # --- 5 ESTADOS CRÍTICOS ---
    elif estado == "FRICCION_SEVERA":
        t, v = np.random.normal(95, 4), np.random.normal(28, 3)
    elif estado == "DESALINEACION_SEVERA":
        t, v = np.random.normal(60, 3), np.random.normal(45, 4)
    elif estado == "FALLA_REFRIGERACION":
        t, v = np.random.normal(115, 5), np.random.normal(15, 2) # ¡AQUÍ ESTÁ LA TEMPERATURA EXTREMA!
    elif estado == "SOLTURA_BASE":
        t, v = np.random.normal(48, 3), np.random.normal(65, 5)
    elif estado == "ROTURA_ENGRANAJE":
        t, v = np.random.normal(88, 5), np.random.normal(58, 6)
        
    else:
        # Si no coincide el nombre, envía normal
        t, v = 40, 10

    ts = datetime.utcnow().isoformat() + "Z"
    return [
        {"id_sensor": f"S-TEMP-{maquina_id}", "valor": round(t, 2), "timestamp": ts},
        {"id_sensor": f"S-VIB-{maquina_id}", "valor": round(v, 2), "timestamp": ts}
    ]

if __name__ == "__main__":
    print("🚀 Simulador Numérico Iniciado (V2.0 Calibrado con 10 fallas)...")
    time.sleep(15) 
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    while True:
        maquinas = obtener_configuracion_viva()
        for id_maq, estado in maquinas:
            lecturas = generar_lectura(id_maq, estado)
            for dato in lecturas:
                producer.send('telemetria_sensores', value=dato)
        
        producer.flush()
        time.sleep(1)