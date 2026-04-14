-- 1. DIMENSIÓN: MÁQUINAS (20 unidades)
CREATE TABLE IF NOT EXISTS maquinas (
    id_maquina VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100),
    sector VARCHAR(50),
    fecha_instalacion DATE DEFAULT CURRENT_DATE
);

-- 2. DIMENSIÓN: SENSORES (2 por máquina = 40 sensores)
CREATE TABLE IF NOT EXISTS sensores (
    id_sensor VARCHAR(50) PRIMARY KEY,
    id_maquina VARCHAR(20) REFERENCES maquinas(id_maquina),
    tipo_medicion VARCHAR(50), -- 'Temperatura' o 'Vibracion'
    unidad_medida VARCHAR(10)
);


-- ==========================================================
-- 1. CAPA DE TELEMETRÍA (DATOS EN TIEMPO REAL)
-- ==========================================================

-- Almacena cada dato que sale de Spark (Limpieza inicial)
CREATE TABLE IF NOT EXISTS telemetria_limpia (
    id_sensor VARCHAR(50),
    valor DOUBLE PRECISION,
    timestamp_evento TIMESTAMP,
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Almacena predicciones fila por fila (para los gráficos de líneas)
CREATE TABLE IF NOT EXISTS predicciones_ia (
    id_sensor VARCHAR(50),
    valor_leido DOUBLE PRECISION,
    falla_predicha INTEGER, -- 0 o 1
    timestamp_prediccion TIMESTAMP
);

-- ==========================================================
-- 2. CAPA ANALÍTICA (VENTANAS DE TIEMPO / DECISIÓN)
-- ==========================================================

-- Almacena el resumen de 1 minuto procesado por Spark
CREATE TABLE IF NOT EXISTS predicciones_ia_ventanas (
    id_sensor VARCHAR(50),
    valor_promedio DOUBLE PRECISION,
    valor_maximo DOUBLE PRECISION,
    timestamp_ventana TIMESTAMP,
    decision_id INTEGER -- 0: Normal, 1: Riesgo, 2: Parada
);

-- ==========================================================
-- 3. CAPA DE CONTROL (INGENIERÍA DEL CAOS)
-- ==========================================================

-- Controla el estado de las máquinas desde la interfaz web
CREATE TABLE IF NOT EXISTS estado_maquinas (
    id_maquina VARCHAR(10) PRIMARY KEY,
    estado_actual VARCHAR(50) DEFAULT 'NORMAL',
    ultima_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inicialización de las 20 máquinas en estado óptimo
INSERT INTO estado_maquinas (id_maquina)
SELECT 'M-' || lpad(i::text, 3, '0') FROM generate_series(1, 20) s(i)
ON CONFLICT (id_maquina) DO NOTHING;

DO $$
DECLARE
    i INT;
    maq_id VARCHAR(20);
BEGIN
    FOR i IN 1..20 LOOP
        maq_id := 'M-' || LPAD(i::TEXT, 3, '0');
        
        INSERT INTO maquinas (id_maquina, nombre, sector) 
        VALUES (maq_id, 'Brazo Robótico ' || i, 'Sector Ensamblaje') ON CONFLICT DO NOTHING;
        
        INSERT INTO sensores (id_sensor, id_maquina, tipo_medicion, unidad_medida) 
        VALUES ('S-TEMP-' || maq_id, maq_id, 'Temperatura', '°C') ON CONFLICT DO NOTHING;
        
        INSERT INTO sensores (id_sensor, id_maquina, tipo_medicion, unidad_medida) 
        VALUES ('S-VIB-' || maq_id, maq_id, 'Vibracion', 'Hz') ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

-- Insertamos las 20 máquinas por defecto en estado NORMAL
INSERT INTO estado_maquinas (id_maquina)
SELECT 'M-' || lpad(i::text, 3, '0') FROM generate_series(1, 20) s(i)
ON CONFLICT (id_maquina) DO NOTHING;