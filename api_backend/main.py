from fastapi import FastAPI, HTTPException
import psycopg2
import pandas as pd

app = FastAPI(title="API Predictiva Industria 4.0")

def get_db_connection():
    # Se conecta al contenedor de la base de datos
    return psycopg2.connect(host="iot-postgres", port="5432", dbname="industria40", user="admin", password="admin123")

@app.get("/api/telemetria/{id_maquina}")
def obtener_telemetria(id_maquina: str, limite: int = 60): # Subimos a 60
    try:
        conn = get_db_connection()
        query = f"""
            SELECT id_sensor, timestamp_prediccion, valor_leido, falla_predicha 
            FROM predicciones_ia 
            WHERE id_sensor LIKE '%{id_maquina}%' 
            ORDER BY timestamp_prediccion DESC LIMIT {limite};
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Invertimos para el gráfico
        df = df.iloc[::-1]
        df['timestamp_prediccion'] = df['timestamp_prediccion'].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/planta/estado")
def obtener_estado_planta():
    try:
        conn = get_db_connection()
        query = """
            SELECT falla_predicha, COUNT(*) as total 
            FROM (SELECT falla_predicha FROM predicciones_ia ORDER BY timestamp_prediccion DESC LIMIT 40) as ultimos
            GROUP BY falla_predicha;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/planta/estado_actual")
def obtener_estado_actual_todas():
    # Devuelve la última lectura de CADA sensor en la planta
    try:
        conn = get_db_connection()
        query = """
            SELECT DISTINCT ON (id_sensor) id_sensor, timestamp_prediccion, valor_leido, falla_predicha
            FROM predicciones_ia
            ORDER BY id_sensor, timestamp_prediccion DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        df['timestamp_prediccion'] = df['timestamp_prediccion'].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/planta/historico_10m")
def obtener_historico_10m():
    try:
        conn = get_db_connection()
        # Buscamos alertas (falla=1) de los últimos 10 minutos, agrupadas por máquina
        query = """
            SELECT 
                substring(id_sensor from 'M-\d{3}') AS id_maquina,
                COUNT(*) as total_fallas
            FROM predicciones_ia
            WHERE falla_predicha = 1 
              AND timestamp_prediccion >= NOW() - INTERVAL '10 minutes'
            GROUP BY id_maquina
            ORDER BY total_fallas DESC
            LIMIT 10;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))