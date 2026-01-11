-- Script para renombrar la tabla contacts y sus columnas
-- Autor: Antigravity
-- Fecha: 2025-12-29
-- 
-- Renombra:
--   - Tabla: contacts → contatos
--   - Columna: contactid → contactoid
--   - Columna: contact → contacto
--   - Columna: reference → referencia

BEGIN;

-- 1. Renombrar la tabla
ALTER TABLE contacts RENAME TO contatos;

-- 2. Renombrar las columnas
ALTER TABLE contatos RENAME COLUMN contactid TO contactoid;
ALTER TABLE contatos RENAME COLUMN contact TO contacto;
ALTER TABLE contatos RENAME COLUMN reference TO referencia;

-- 3. Verificar los cambios
SELECT 
    column_name, 
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'contatos'
ORDER BY ordinal_position;

COMMIT;

-- Fin del script
