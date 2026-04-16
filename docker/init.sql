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

-- 3. CAPA DE TELEMETRÍA Y PREDICCIONES
CREATE TABLE IF NOT EXISTS telemetria_limpia (
    id_sensor VARCHAR(50),
    valor DOUBLE PRECISION,
    timestamp_evento TIMESTAMP,
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predicciones_ia (
    id_sensor VARCHAR(50),
    valor_leido DOUBLE PRECISION,
    falla_predicha INTEGER,
    timestamp_prediccion TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predicciones_ia_ventanas (
    id_sensor VARCHAR(50),
    valor_promedio DOUBLE PRECISION,
    valor_maximo DOUBLE PRECISION,
    timestamp_ventana TIMESTAMP,
    decision_id INTEGER
);

-- 4. CAPA DE CONTROL (INGENIERÍA DEL CAOS)
CREATE TABLE IF NOT EXISTS estado_maquinas (
    id_maquina VARCHAR(10) PRIMARY KEY,
    estado_actual VARCHAR(50) DEFAULT 'NORMAL',
    ultima_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. POBLADO DINÁMICO INICIAL
DO $$
DECLARE
    i INT;
    maq_id VARCHAR(20);
BEGIN
    FOR i IN 1..20 LOOP
        maq_id := 'M-' || LPAD(i::TEXT, 3, '0');
        
        INSERT INTO maquinas (id_maquina, nombre, sector) 
        VALUES (maq_id, 'Motor Industrial ' || i, 'Planta Principal') 
        ON CONFLICT DO NOTHING;
        
        INSERT INTO sensores (id_sensor, id_maquina, tipo_medicion, unidad_medida) 
        VALUES ('S-TEMP-' || maq_id, maq_id, 'Temperatura', '°C') ON CONFLICT DO NOTHING;
        
        INSERT INTO sensores (id_sensor, id_maquina, tipo_medicion, unidad_medida) 
        VALUES ('S-VIB-' || maq_id, maq_id, 'Vibracion', 'Hz') ON CONFLICT DO NOTHING;

        INSERT INTO estado_maquinas (id_maquina, estado_actual)
        VALUES (maq_id, 'NORMAL') ON CONFLICT DO NOTHING;
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS log_eventos (
    id SERIAL PRIMARY KEY,
    timestamp_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_evento VARCHAR(50), -- 'SISTEMA_IA', 'USUARIO_CAOS', 'NOTIFICACION'
    maquina_id VARCHAR(20),
    descripcion TEXT
);

-- TABLA DE MANTENIMIENTO PROGRAMADO
CREATE TABLE IF NOT EXISTS mantenimiento_programado (
    id SERIAL PRIMARY KEY,
    maquina_id VARCHAR(20),
    fecha_sugerida DATE,
    motivo VARCHAR(255),
    estado VARCHAR(20) DEFAULT 'PENDIENTE' -- 'PENDIENTE' o 'COMPLETADO'
);