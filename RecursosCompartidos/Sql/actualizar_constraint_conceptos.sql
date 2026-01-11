-- Script para actualizar el constraint UNIQUE de la tabla conceptos
-- Cambia de 'concepto' a 'claveconcepto'

-- 1. Eliminar el constraint UNIQUE actual sobre 'concepto'
ALTER TABLE conceptos DROP CONSTRAINT IF EXISTS conceptos_concepto_key;

-- 2. Agregar el nuevo constraint UNIQUE sobre 'claveconcepto'
ALTER TABLE conceptos ADD CONSTRAINT conceptos_claveconcepto_key UNIQUE (claveconcepto);

-- Verificar el cambio
SELECT constraint_name, column_name
FROM information_schema.constraint_column_usage
WHERE table_name = 'conceptos' AND constraint_name LIKE '%unique%' OR constraint_name LIKE '%key';
