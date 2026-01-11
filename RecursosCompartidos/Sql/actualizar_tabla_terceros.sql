-- ============================================================================
-- Script para actualizar la tabla TERCEROS con constraints correctos
-- ============================================================================
-- Autor: Antigravity
-- Fecha: 2025-12-30
-- Descripción: 
--   Modifica la tabla terceros para permitir:
--   1. Un tercero con múltiples descripciones (ej: Bancolombia -> cuota de manejo, intereses)
--   2. Referencias únicas cuando existen (cuentas bancarias, celulares)
--   3. Combinación (tercero, descripcion) única cuando no hay referencia
-- ============================================================================

BEGIN;

-- Paso 1: Eliminar el constraint único actual si existe
ALTER TABLE terceros 
DROP CONSTRAINT IF EXISTS terceros_tercero_descripcion_key;

-- Paso 2: Asegurar que el campo referencia tenga valor por defecto
ALTER TABLE terceros 
ALTER COLUMN referencia SET DEFAULT '';

-- Paso 3: Actualizar registros con referencia NULL a string vacío
UPDATE terceros 
SET referencia = '' 
WHERE referencia IS NULL;

-- Paso 4: Crear índice único para referencias cuando NO están vacías
-- Este garantiza que cada cuenta bancaria o celular sea única
CREATE UNIQUE INDEX IF NOT EXISTS terceros_referencia_unique_idx 
ON terceros (referencia) 
WHERE referencia != '';

-- Paso 5: Crear índice único para (tercero, descripcion) cuando referencia está vacía
-- Esto permite: Bancolombia + "cuota de manejo", Bancolombia + "intereses", etc.
CREATE UNIQUE INDEX IF NOT EXISTS terceros_tercero_descripcion_unique_idx 
ON terceros (tercero, descripcion) 
WHERE referencia = '';

COMMIT;

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

-- Verificar índices creados
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'terceros';

-- Ejemplos de datos válidos después de esta migración:
-- ┌───────────┬─────────────────────┬──────────────┬──────────────┐
-- │ terceroid │ tercero             │ descripcion  │ referencia   │
-- ├───────────┼─────────────────────┼──────────────┼──────────────┤
-- │ 1         │ Bancolombia         │ Cuota Manejo │              │ ✓ Válido
-- │ 2         │ Bancolombia         │ Intereses    │              │ ✓ Válido (mismo tercero, diferente descripcion)
-- │ 3         │ Juan Pérez          │ Transferencia│ 3001234567   │ ✓ Válido (referencia única)
-- │ 4         │ María López         │ Pago         │ 3009876543   │ ✓ Válido (otra referencia única)
-- └───────────┴─────────────────────┴──────────────┴──────────────┘

-- Ejemplos de datos NO válidos (generarían error):
-- ┌───────────┬─────────────────────┬──────────────┬──────────────┐
-- │ terceroid │ tercero             │ descripcion  │ referencia   │
-- ├───────────┼─────────────────────┼──────────────┼──────────────┤
-- │ 5         │ Bancolombia         │ Cuota Manejo │              │ ✗ Error (ya existe id=1 con tercero+descripcion)
-- │ 6         │ Pedro Gomez         │ Otro         │ 3001234567   │ ✗ Error (referencia ya existe en id=3)
-- └───────────┴─────────────────────┴──────────────┴──────────────┘
