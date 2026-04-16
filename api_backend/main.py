from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List

app = FastAPI(title="API Industria 4.0 - Gestión de Activos")

# Configuración de conexión
DB_CONFIG = {
    "host": "iot-postgres",
    "database": "industria40",
    "user": "admin",
    "password": "admin123"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@app.get("/maquinas/estado-general")
def get_estado_general():
    """Obtiene el resumen de todas las máquinas cruzando estado actual y última predicción."""
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        SELECT 
            em.id_maquina, 
            em.estado_actual, 
            p.valor_promedio, 
            p.valor_maximo, 
            p.decision_id,
            p.timestamp_ventana
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
    
    # Lógica de corrección "APAGADA"
    for item in data:
        if item['estado_actual'] == 'APAGADA':
            item['decision_id'] = -1 # Código interno para mostrar gris/apagado
    
    return data

@app.get("/maquinas/tiempo-real/{id_maquina}")
def get_tiempo_real(id_maquina: str):
    """Obtiene los últimos datos crudos de los sensores (para velocímetros)."""
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        SELECT id_sensor, valor, timestamp_evento 
        FROM telemetria_limpia 
        WHERE id_sensor LIKE %s 
        ORDER BY timestamp_evento DESC LIMIT 2;
    """
    cur.execute(query, (f"%{id_maquina}%",))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.get("/maquinas/historial/{id_maquina}")
def get_historial(id_maquina: str):
    """Obtiene las últimas 30 ventanas de análisis de la IA."""
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        SELECT timestamp_ventana, valor_promedio, valor_maximo, decision_id 
        FROM predicciones_ia_ventanas 
        WHERE id_sensor = %s 
        ORDER BY timestamp_ventana DESC LIMIT 30;
    """
    cur.execute(query, (id_maquina,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


from pydantic import BaseModel

class LogEvento(BaseModel):
    tipo_evento: str
    maquina_id: str
    descripcion: str

@app.post("/logs/")
def registrar_log(evento: LogEvento):
    """Guarda un evento en la tabla de auditoría."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO log_eventos (tipo_evento, maquina_id, descripcion) VALUES (%s, %s, %s)",
        (evento.tipo_evento, evento.maquina_id, evento.descripcion)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "registrado"}

@app.get("/logs/")
def obtener_logs():
    """Lee los últimos 50 eventos para la página de auditoría."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM log_eventos ORDER BY timestamp_evento DESC LIMIT 50;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data