import json
import time
import numpy as np
import psycopg2
from kafka import KafkaProducer
from datetime import datetime

"""
=============================================================================
MÓDULO: Productor de Visión IoT (Cámara Térmica)
VERSIÓN: 2.5
DESCRIPCIÓN: 
Simula una matriz de píxeles térmicos de las máquinas. Envía matrices 
multidimensionales a través de Kafka simulando un flujo de video a bajos FPS.
CONTEXTO DE INTELIGENCIA ARTIFICIAL:
Los frames generados son datos no estructurados.
Actualmente preparados para: Mapas de calor en tiempo real (Visualización).
Futuro: Redes Neuronales Convolucionales (CNN) para detectar patrones de 
sobrecalentamiento o fisuras en el material antes de que los sensores numéricos 
lo detecten.
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
        print(f"🔄 Esperando Postgres para configuración visual...")
        return []

def generar_frame_termico(estado, size=(64, 64)):
    base = np.random.normal(0.3, 0.05, size)
    x, y = np.meshgrid(np.linspace(-1, 1, size[0]), np.linspace(-1, 1, size[1]))
    
    # --- ALINEACIÓN EXACTA CON LOS BOTONES DE LA CONSOLA CAOS ---
    
    if estado == "NORMAL" or estado == "APAGADA":
        # Ligero calor central normal de operación (Apagada es frío, pero visualmente normal)
        calor = np.exp(-(x**2 + y**2) / 0.5) * 0.2
        
    # Agrupación Visual: FRICCIÓN (Foco Central)
    elif estado == "FRICCION_LEVE" or estado == "FRICCION_SEVERA" or estado == "FALTA_LUBRICACION" or estado == "SOBRECARGA_LIGERA" or estado == "ROTURA_ENGRANAJE":
        calor = np.exp(-(x**2 + y**2) / 0.1) * 0.8
        
    # Agrupación Visual: SOPORTES (Calor Lateral)
    elif estado == "DESALINEACION_LEVE" or estado == "DESALINEACION_SEVERA" or estado == "SOLTURA_BASE" or estado == "DESGASTE_RODAMIENTO":
        calor = np.exp(-((x-0.7)**2 + (y-0.7)**2)/0.15)*0.6 + np.exp(-((x+0.7)**2 + (y+0.7)**2)/0.15)*0.6
        
    # Agrupación Visual: COLAPSO (Calor Total)
    elif estado == "FALLA_REFRIGERACION":
        calor = (np.exp(-(x**2 + y**2) / 1.5) * 0.7) + (np.random.uniform(0, 0.2, size)) 
        
    else:
        # Estado de falla genérico: un poco de sobrecarga
        calor = np.exp(-(x**2 + y**2) / 0.3) * 0.5 
        
    img = np.clip(base + calor, 0, 1)
    return img.tolist() 

if __name__ == "__main__":
    print("📸 Cámara Térmica IoT Iniciada (V2.0 Calibrada con 10 Fallas). Conectando a Kafka...")
    time.sleep(10) # Margen de espera
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    while True:
        maquinas = obtener_configuracion_viva()
        ts = datetime.utcnow().isoformat() + "Z"
        
        for id_maq, estado in maquinas:
            # Generamos 1 frame por máquina
            frame = generar_frame_termico(estado)
            payload = {
                "id_maquina": id_maq,
                "timestamp": ts,
                "frame_matriz": frame
            }
            producer.send('video_termico', value=payload)
            
        producer.flush()
        # Transmitimos a 0.5 FPS para no saturar la red local, el dashboard hará el resto
        time.sleep(2)