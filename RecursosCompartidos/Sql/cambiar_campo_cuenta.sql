-- Script para cambiar el tipo de dato del campo 'cuenta' en la tabla 'cuentas'
-- De TEXT a VARCHAR(50)

-- Cambiar el tipo de dato del campo 'cuenta'
ALTER TABLE cuentas 
ALTER COLUMN cuenta TYPE VARCHAR(50);

-- Verificar el cambio
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'cuentas' AND column_name = 'cuenta';
