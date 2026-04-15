import json
import time
import random
import numpy as np
from datetime import datetime
from kafka import KafkaProducer
import psycopg2

def get_estado_maquinas():
    try:
        conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute("SELECT id_sensor, estado FROM estado_maquinas;")
        estados = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()
        return estados
    except Exception as e:
        print(f"Esperando a Postgres... {e}")
        return {}

def generar_telemetria(maquina_id, estado):
    if estado == "NORMAL":
        temp = np.random.normal(40, 2)
        vib = np.random.normal(10, 1)
    elif estado == "FRICCION_TERMICA":
        temp = np.random.normal(85, 4)
        vib = np.random.normal(15, 2)
    elif estado == "DESALINEACION":
        temp = np.random.normal(50, 3)
        vib = np.random.normal(35, 4)
    elif estado == "FALLA_REFRIGERACION":
        temp = np.random.normal(95, 3)
        vib = np.random.normal(12, 1)
    elif estado == "SOLTURA_BASE":
        temp = np.random.normal(42, 2)
        vib = np.random.normal(45, 5)
    elif estado == "APAGADA":
        temp = np.random.normal(20, 0.5)
        vib = np.random.normal(0, 0.1)
    else:
        temp, vib = 40, 10 # Default fallback

    timestamp = datetime.utcnow().isoformat() + "Z"
    
    return [
        {"id_sensor": f"S-TEMP-{maquina_id}", "valor": round(temp, 2), "timestamp": timestamp},
        {"id_sensor": f"S-VIB-{maquina_id}", "valor": round(vib, 2), "timestamp": timestamp}
    ]

if __name__ == "__main__":
    print("Iniciando Productor de IoT Inteligente...")
    time.sleep(15) # Esperar que Kafka inicie
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    while True:
        estados = get_estado_maquinas()
        if not estados:
            time.sleep(2)
            continue

        for maquina_id, estado in estados.items():
            datos = generar_telemetria(maquina_id, estado)
            for dato in datos:
                producer.send('telemetria_sensores', value=dato)
        
        producer.flush()
        time.sleep(1) # Enviar datos cada segundo