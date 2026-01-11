-- Agregar columna es_traslado a la tabla grupos
ALTER TABLE grupos ADD COLUMN IF NOT EXISTS es_traslado BOOLEAN DEFAULT FALSE;

-- Inicializar el campo basado en el nombre actual del grupo
UPDATE grupos SET es_traslado = TRUE WHERE grupo ILIKE '%traslado%';
