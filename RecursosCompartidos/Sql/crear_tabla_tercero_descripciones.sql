-- ==============================================================================
-- RECREAR TABLA tercero_descripciones (Estructura Simplificada)
-- ==============================================================================
-- Elimina la tabla existente y la recrea sin el campo tercero_des

-- Eliminar tabla existente
DROP TABLE IF EXISTS tercero_descripciones CASCADE;

-- Crear tabla con estructura simplificada
CREATE TABLE tercero_descripciones (
    id SERIAL PRIMARY KEY,
    terceroid INT NOT NULL,
    descripcion TEXT,
    referencia TEXT,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_tercero_master 
        FOREIGN KEY (terceroid) 
        REFERENCES terceros(terceroid)
);

-- Índice para búsqueda por descripción
CREATE INDEX idx_tercero_descripciones_descripcion 
    ON tercero_descripciones(descripcion) 
    WHERE activa = TRUE;

-- Índice para búsqueda por referencia
CREATE INDEX idx_tercero_descripciones_referencia 
    ON tercero_descripciones(referencia) 
    WHERE referencia IS NOT NULL AND activa = TRUE;

-- Índice para ordenamiento por tercero maestro
CREATE INDEX idx_tercero_descripciones_terceroid 
    ON tercero_descripciones(terceroid);
