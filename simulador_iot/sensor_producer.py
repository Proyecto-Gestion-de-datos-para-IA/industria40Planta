import time
import json
import random
import psycopg2
from kafka import KafkaProducer
from datetime import datetime
import numpy as np

# Configuración de Kafka y BD
KAFKA_BROKER = 'kafka:9092'
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

def obtener_estados_db():
    estados = {}
    try:
        conn = psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")
        cur = conn.cursor()
        cur.execute("SELECT id_maquina, estado_actual FROM estado_maquinas;")
        for fila in cur.fetchall():
            estados[fila[0]] = fila[1]
        conn.close()
    except Exception as e:
        print(f"Error conectando a BD: {e}")
    return estados

print("Iniciando Productor de IoT Inteligente...")
estados_maquinas = {}
contador_ciclos = 0

while True:
    # Actualizamos los estados desde la BD cada 5 ciclos (para no saturar Postgres)
    if contador_ciclos % 5 == 0:
        nuevos_estados = obtener_estados_db()
        if nuevos_estados:
            estados_maquinas = nuevos_estados
    
    for i in range(1, 21):
        maquina_id = f"M-{str(i).zfill(3)}"
        estado = estados_maquinas.get(maquina_id, "NORMAL")
        
        # --- MOTOR MATEMÁTICO DE FALLAS ---
        if estado == "NORMAL":
            # Operación óptima: Temp ~40°C, Vib ~10Hz
            temp = np.random.normal(40, 2)
            vib = np.random.normal(10, 1)
        elif estado == "FRICCION_TERMICA":
            # Falla de lubricación: Temp altísima, Vib sube un poco
            temp = np.random.normal(85, 4)
            vib = np.random.normal(15, 2)
        elif estado == "DESALINEACION":
            # Falla mecánica: Vib altísima, Temp sube un poco
            temp = np.random.normal(50, 3)
            vib = np.random.normal(35, 4)
        elif estado == "FALLA_REFRIGERACION":
            # Muchísimo calor, vibración normal
            temp = np.random.normal(92, 3)
            vib = np.random.normal(11, 1)
        elif estado == "SOLTURA_BASE":
            # Temperatura normal, vibración errática y altísima
            temp = np.random.normal(45, 2)
            vib = np.random.normal(42, 6)
        elif estado == "FALLA_CATASTROFICA":
            # Todo al máximo, a punto de explotar
            temp = np.random.normal(95, 5)
            vib = np.random.normal(45, 5)
            
        # Enviamos los datos asegurando que no existan valores negativos
        temp = max(0, temp)
        vib = max(0, vib)

        timestamp = datetime.utcnow().isoformat()
        
        producer.send('telemetria_sensores', {'id_sensor': f'S-TEMP-{maquina_id}', 'valor': temp, 'timestamp': timestamp})
        producer.send('telemetria_sensores', {'id_sensor': f'S-VIB-{maquina_id}', 'valor': vib, 'timestamp': timestamp})

    contador_ciclos += 1
    time.sleep(1) # Generamos 40 mensajes por segundo