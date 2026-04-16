import json
import time
import numpy as np
from datetime import datetime
from kafka import KafkaProducer
import psycopg2

def obtener_configuracion_viva():
    """Lee la lista de máquinas y su estado directamente de Postgres."""
    try:
        conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute("SELECT id_maquina, estado_actual FROM estado_maquinas;")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"🔄 Esperando conexión con Postgres para leer configuración...")
        return []

def generar_lectura(maquina_id, estado):
    # Lógica de estados basada en tus nuevas categorías
    if estado == "NORMAL":
        t, v = np.random.normal(40, 2), np.random.normal(10, 1)
    elif estado == "FRICCION_TERMICA":
        t, v = np.random.normal(85, 4), np.random.normal(15, 2)
    elif estado == "DESALINEACION":
        t, v = np.random.normal(50, 3), np.random.normal(35, 4)
    elif estado == "FALLA_REFRIGERACION":
        t, v = np.random.normal(95, 3), np.random.normal(12, 1)
    elif estado == "SOLTURA_BASE":
        t, v = np.random.normal(42, 2), np.random.normal(45, 5)
    elif estado == "APAGADA":
        t, v = np.random.normal(22, 0.5), np.random.normal(0, 0.1)
    else:
        t, v = 40, 10

    ts = datetime.utcnow().isoformat() + "Z"
    return [
        {"id_sensor": f"S-TEMP-{maquina_id}", "valor": round(t, 2), "timestamp": ts},
        {"id_sensor": f"S-VIB-{maquina_id}", "valor": round(v, 2), "timestamp": ts}
    ]

if __name__ == "__main__":
    print("🚀 Simulador Dinámico Iniciado...")
    time.sleep(20) # Margen para que Kafka y Postgres despierten
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    while True:
        maquinas = obtener_configuracion_viva()
        for id_maq, estado in maquinas:
            for dato in generar_lectura(id_maq, estado):
                producer.send('telemetria_sensores', value=dato)
        
        producer.flush()
        time.sleep(1)