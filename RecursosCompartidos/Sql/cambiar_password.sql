-- Script SQL para cambiar la contraseña del usuario postgres
-- Ejecutar en pgAdmin4 Query Tool

-- Cambiar contraseña del usuario postgres a 'SLB'
ALTER USER postgres WITH PASSWORD 'SLB';

-- Verificar que el cambio fue exitoso (no mostrará la contraseña)
SELECT usename FROM pg_user WHERE usename = 'postgres';
