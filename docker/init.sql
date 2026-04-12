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

-- 3. HECHOS: DATA LIMPIA (Histórico procesado por Spark)
CREATE TABLE IF NOT EXISTS telemetria_limpia (
    id SERIAL PRIMARY KEY,
    id_sensor VARCHAR(50) REFERENCES sensores(id_sensor),
    timestamp_evento TIMESTAMP,
    valor_medicion FLOAT
);

-- 4. HECHOS: DATA CON IA (Resultados de la predicción)
CREATE TABLE IF NOT EXISTS predicciones_ia (
    id SERIAL PRIMARY KEY,
    id_sensor VARCHAR(50) REFERENCES sensores(id_sensor),
    timestamp_prediccion TIMESTAMP,
    valor_leido FLOAT,
    probabilidad_falla FLOAT, -- Resultado del modelo
    falla_predicha INTEGER     -- 0: Normal, 1: Alerta
);

-- POBLAR DIMENSIONES (20 Máquinas y sus 40 sensores)
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