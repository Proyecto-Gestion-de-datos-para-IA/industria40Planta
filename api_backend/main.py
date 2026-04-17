from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import List

app = FastAPI(title="API Industria 4.0 - Gestión Bellohorizonte")

DB_CONFIG = {"host": "iot-postgres", "database": "industria40", "user": "admin", "password": "admin123"}

class LogEvento(BaseModel):
    tipo_evento: str
    maquina_id: str
    descripcion: str

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@app.get("/maquinas/estado-general")
def get_estado_general():
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        SELECT em.id_maquina, em.estado_actual, p.valor_promedio, p.valor_maximo, p.decision_id
        FROM estado_maquinas em
        LEFT JOIN (
            SELECT DISTINCT ON (id_sensor) * FROM predicciones_ia_ventanas 
            ORDER BY id_sensor, timestamp_ventana DESC
        ) p ON em.id_maquina = p.id_sensor
        ORDER BY em.id_maquina ASC;
    """
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    conn.close()
    for item in data:
        if item['estado_actual'] == 'APAGADA': item['decision_id'] = -1
    return data

@app.get("/maquinas/tiempo-real/{id_maquina}")
def get_tiempo_real(id_maquina: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_sensor, valor FROM telemetria_limpia WHERE id_sensor LIKE %s ORDER BY timestamp_evento DESC LIMIT 2;", (f"%{id_maquina}%",))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.post("/logs/")
def registrar_log(evento: LogEvento):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO log_eventos (tipo_evento, maquina_id, descripcion) VALUES (%s, %s, %s)",
                (evento.tipo_evento, evento.maquina_id, evento.descripcion))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "ok"}