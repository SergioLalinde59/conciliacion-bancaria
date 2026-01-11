-- ==============================================================================
-- LIMPIAR Y REPOBLAR tercero_descripciones (VERSIÓN FINAL)
-- ==============================================================================

BEGIN;

TRUNCATE TABLE tercero_descripciones RESTART IDENTITY;

-- Crear tabla temporal con datos normalizados
CREATE TEMP TABLE temp_movs AS
SELECT 
    m.terceroid,
    m.descripcion,
    CASE 
        WHEN m.referencia IS NULL THEN NULL
        WHEN TRIM(m.referencia) = '' THEN NULL
        WHEN m.referencia ~ '^\d{1,2}/\d{1,2}/\d{2,4}$' THEN NULL
        ELSE TRIM(m.referencia)
    END as referencia
FROM movimientos m
WHERE m.terceroid IS NOT NULL
  AND m.cuentaid != 1
  AND m.descripcion IS NOT NULL
  AND TRIM(m.descripcion) != ''
  AND TRIM(m.descripcion) != '-';

-- PASO 1: Insertar registros con referencia válida (8+ dígitos)
-- Unicidad por (terceroid, referencia) - La descripción puede variar
INSERT INTO tercero_descripciones (terceroid, descripcion, referencia, activa)
SELECT DISTINCT ON (MIN(terceroid), referencia)
    MIN(terceroid) as terceroid,
    descripcion,
    referencia,
    TRUE
FROM temp_movs
WHERE referencia IS NOT NULL 
  AND referencia ~ '^\d{8,}$'
GROUP BY descripcion, referencia
ORDER BY MIN(terceroid), referencia, descripcion;

-- PASO 2: Insertar registros SIN referencia válida
-- Unicidad por (terceroid, descripcion)
INSERT INTO tercero_descripciones (terceroid, descripcion, referencia, activa)
SELECT 
    MIN(terceroid) as terceroid,
    descripcion,
    NULL,
    TRUE
FROM temp_movs
WHERE referencia IS NULL 
   OR referencia !~ '^\d{8,}$'
GROUP BY descripcion
-- Excluir si ya existe una descripción igual con referencia
HAVING NOT EXISTS (
    SELECT 1 FROM tercero_descripciones td 
    WHERE td.descripcion = temp_movs.descripcion
)
ORDER BY MIN(terceroid), descripcion;

DROP TABLE temp_movs;

COMMIT;

SELECT COUNT(*) as total FROM tercero_descripciones;
