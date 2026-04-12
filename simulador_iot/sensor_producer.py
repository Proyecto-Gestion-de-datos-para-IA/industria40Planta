import json, time, random
from datetime import datetime
from confluent_kafka import Producer

conf = {'bootstrap.servers': "iot-kafka:9092", 'client.id': 'simulador-industrial'}
p = Producer(conf)

# Generar 40 sensores dinámicos
sensores = []
for i in range(1, 21):
    m = f"M-{i:03d}"
    sensores.append({"id": f"S-TEMP-{m}", "tipo": "T"})
    sensores.append({"id": f"S-VIB-{m}", "tipo": "V"})

print("🚀 Enviando ráfagas de 40 sensores a Kafka...")

try:
    while True:
        for s in sensores:
            valor = round(random.uniform(30, 50), 2) if s["tipo"] == "T" else round(random.uniform(5, 15), 2)
            if random.random() < 0.05: valor += 30 # Anomalía para la IA
            
            msg = {"id_sensor": s["id"], "timestamp_evento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "valor_medicion": valor}
            p.produce('telemetria_sensores', value=json.dumps(msg))
        
        p.flush()
        time.sleep(0.5) # Alta frecuencia: ráfaga cada medio segundo
except KeyboardInterrupt:
    pass