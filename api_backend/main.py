from fastapi import FastAPI
import psycopg2
from typing import List
from pydantic import BaseModel

app = FastAPI(title="API Mantenimiento Predictivo")

def get_db_connection():
    return psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")

class EstadoMaquina(BaseModel):
    id_maquina: str
    temp_promedio: float
    vib_promedio: float
    decision_ia: int
    timestamp: str

@app.get("/api/planta/estado_ventanas", response_model=List[EstadoMaquina])
def get_estado_ventanas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (id_sensor) id_sensor, valor_promedio, valor_maximo, decision_id, timestamp_ventana
        FROM predicciones_ia_ventanas ORDER BY id_sensor, timestamp_ventana DESC;
    """)
    rows = cur.fetchall()
    conn.close()
    return [{"id_maquina": r[0], "temp_promedio": round(r[1] or 0, 2), "vib_promedio": round(r[2] or 0, 2), "decision_ia": r[3], "timestamp": str(r[4])} for r in rows]

# --- NUEVO ENDPOINT PARA EL ANÁLISIS INDIVIDUAL ---
@app.get("/api/telemetria/{id_maquina}")
def get_historial_maquina(id_maquina: str):
    """Obtiene las últimas 15 ventanas (15 minutos) de una máquina específica."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT valor_promedio, valor_maximo, decision_id, timestamp_ventana
        FROM predicciones_ia_ventanas
        WHERE id_sensor = %s
        ORDER BY timestamp_ventana DESC LIMIT 15;
    """, (id_maquina,))
    rows = cur.fetchall()
    conn.close()
    
    # Devolvemos la data ordenada cronológicamente (de más antigua a más nueva para el gráfico)
    return [{"temp": round(r[0] or 0, 2), "vib": round(r[1] or 0, 2), "decision": r[2], "hora": str(r[3]).split(" ")[1]} for r in reversed(rows)]