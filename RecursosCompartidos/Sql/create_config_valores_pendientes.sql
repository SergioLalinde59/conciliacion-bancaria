-- Script de migración: Crear tabla config_valores_pendientes
-- Fecha: 2026-01-08
-- Descripción: Almacena IDs de tercero/grupo/concepto que semánticamente significan "pendiente de clasificar"

CREATE TABLE IF NOT EXISTS config_valores_pendientes (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL,  -- 'tercero', 'grupo', 'concepto'
    valor_id INT NOT NULL,
    descripcion VARCHAR(100),
    activo BOOLEAN DEFAULT TRUE,
    UNIQUE(tipo, valor_id)
);

-- Insertar valores iniciales
--INSERT INTO config_valores_pendientes (tipo, valor_id, descripcion, activo) VALUES
--    ('tercero', 196, 'Por identificar', TRUE),
--    ('grupo', 34, 'Por Clasificar', TRUE),
--    ('concepto', 310, 'Por Clasificar', TRUE)
--ON CONFLICT (tipo, valor_id) DO NOTHING;
