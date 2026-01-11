#!/usr/bin/env python3
# Script SIMPLE para resolver el duplicado según instrucciones del usuario

import psycopg2

DB_CONFIG = {'host': 'localhost', 'port': 5433, 'user': 'postgres', 'password': 'SLB', 'database': 'Mvtos'}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("Estado ACTUAL:")
cur.execute("SELECT terceroid, tercero, descripcion, referencia FROM terceros WHERE referencia LIKE '4125857%' ORDER BY terceroid")
for r in cur.fetchall():
    print(f"  ID={r[0]}, Tercero={r[1]}, Ref={r[3]}")

# Actualizar movimientos: todos con TerceroID=122 → cambiar a 116
print("\nActualizando movimientos...") 
cur.execute("UPDATE movimientos SET TerceroID = 116 WHERE TerceroID = 122")
print(f"  ✓ {cur.rowcount} movimientos actualizados")

# Eliminar tercero 122
print("Eliminando tercero 122...")
cur.execute("DELETE FROM terceros WHERE terceroid = 122")
print(f"  ✓ Tercero 122 eliminado")

conn.commit()

print("\nEstado FINAL:")
cur.execute("SELECT terceroid, tercero, descripcion, referencia FROM terceros WHERE referencia LIKE '4125857%' ORDER BY terceroid")
for r in cur.fetchall():
    print(f"  ID={r[0]}, Tercero={r[1]}, Ref={r[3]}")

conn.close()
print("\n✓ COMPLETADO")
