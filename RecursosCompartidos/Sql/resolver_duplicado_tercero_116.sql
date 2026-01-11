-- ============================================================================
-- Script para resolver duplicados en tabla terceros
-- ============================================================================
-- Eliminar tercero duplicado ID=116 y reasignar movimientos a ID=122
-- ============================================================================

BEGIN;

-- Paso 1: Actualizar movimiento ID=95 para usar tercero ID=122 en vez de 116
UPDATE movimientos
SET TerceroID = 122
WHERE Id = 95 AND TerceroID = 116;

-- Verificar el cambio
SELECT Id, Fecha, Descripcion, TerceroID 
FROM movimientos 
WHERE Id = 95;

-- Paso 2: Verificar si hay otros movimientos usando tercero ID=116
SELECT COUNT(*) as movimientos_con_tercero_116
FROM movimientos
WHERE TerceroID = 116;

-- Paso 3: Si no hay otros movimientos, eliminar el tercero ID=116
DELETE FROM terceros
WHERE terceroid = 116;

-- Verificar que se eliminó
SELECT COUNT(*) as terceros_con_id_116
FROM terceros
WHERE terceroid = 116;

COMMIT;

-- ============================================================================
-- VERIFICACIÓN FINAL
-- ============================================================================

-- Ver detalles del movimiento actualizado
SELECT 
    m.Id,
    m.Fecha,
    m.Descripcion,
    m.Referencia,
    t.terceroid,
    t.tercero,
    t.descripcion as tercero_descripcion,
    t.referencia as tercero_referencia
FROM movimientos m
LEFT JOIN terceros t ON m.TerceroID = t.terceroid
WHERE m.Id = 95;

-- Verificar que no quedan duplicados en referencia
SELECT referencia, COUNT(*) as cantidad
FROM terceros
WHERE referencia = '41258577351'
GROUP BY referencia;
