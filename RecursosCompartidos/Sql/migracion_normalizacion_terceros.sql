-- ==============================================================================
-- SCRIPT DE MIGRACIÓN - Poblar tercero_descripciones
-- ==============================================================================
-- Copia cada registro de terceros a tercero_descripciones
-- SIN modificar la tabla terceros original

BEGIN;

-- Poblar tercero_descripciones con todos los registros de terceros
INSERT INTO tercero_descripciones (terceroid, descripcion, referencia, activa)
SELECT 
    terceroid,
    descripcion,
    referencia,
    activa
FROM terceros
WHERE activa = TRUE
ORDER BY terceroid;

COMMIT;

-- ==============================================================================
-- FIN DEL SCRIPT
-- ==============================================================================
