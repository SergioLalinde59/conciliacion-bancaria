-- =====================================================
-- Script para renombrar columnas en tabla movimientos
-- Fecha: 2025-12-30
-- Objetivo: Renombrar CurencyID -> MonedaID y AccountID -> CuentaID
-- =====================================================

-- Nota: Este script renombra las columnas y sus constraints
-- Asegúrate de tener un respaldo antes de ejecutar

BEGIN;

-- 1. Renombrar columna CurencyID a MonedaID
ALTER TABLE movimientos 
RENAME COLUMN CurencyID TO MonedaID;

-- 2. Renombrar columna AccountID a CuentaID
ALTER TABLE movimientos 
RENAME COLUMN AccountID TO CuentaID;

-- 3. Renombrar constraint de foreign key para MonedaID
ALTER TABLE movimientos 
RENAME CONSTRAINT fk_currency TO fk_moneda;

-- 4. Renombrar constraint de foreign key para CuentaID
ALTER TABLE movimientos 
RENAME CONSTRAINT fk_account TO fk_cuenta;

-- Verificar los cambios
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'movimientos' 
  AND column_name IN ('MonedaID', 'CuentaID')
ORDER BY column_name;

-- Verificar constraints
SELECT conname 
FROM pg_constraint 
WHERE conrelid = 'movimientos'::regclass 
  AND conname IN ('fk_moneda', 'fk_cuenta')
ORDER BY conname;

COMMIT;

-- =====================================================
-- Fin del script
-- =====================================================
