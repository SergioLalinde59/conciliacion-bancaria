-- ============================================
-- Script para renombrar tabla contactos a terceros
-- Base de datos: Mvtos
-- Fecha: 2025-12-29
-- ============================================

-- PASO 1: Renombrar columna ContactID en tabla movimientos
ALTER TABLE movimientos 
RENAME COLUMN ContactID TO TerceroID;

-- PASO 2: Eliminar constraint foreign key existente
ALTER TABLE movimientos 
DROP CONSTRAINT IF EXISTS fk_contact;

-- PASO 3: Renombrar tabla contactos a terceros
ALTER TABLE contactos 
RENAME TO terceros;

-- PASO 4: Renombrar columnas en tabla terceros
ALTER TABLE terceros 
RENAME COLUMN contactoid TO terceroid;

ALTER TABLE terceros 
RENAME COLUMN contacto TO tercero;

-- NOTA: Las columnas 'referencia' y 'descripcion' se mantienen sin cambios

-- PASO 5: Recrear foreign key constraint con nuevo nombre
ALTER TABLE movimientos 
ADD CONSTRAINT fk_tercero 
FOREIGN KEY (TerceroID) REFERENCES terceros(terceroid);

-- ============================================
-- Script completado exitosamente
-- ============================================
