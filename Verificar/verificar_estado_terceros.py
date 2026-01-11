#!/usr/bin/env python3
import psycopg2
DB_CONFIG = {'host': 'localhost', 'port': 5433, 'user': 'postgres', 'password': 'SLB', 'database': 'Mvtos'}
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("VERIFICACIÓN ESTADO ACTUAL")
print("="*70)

# Ver terceros con referencia
print("\nTerceros con referencia 41258577351:")
cur.execute("SELECT terceroid, tercero, descripcion, referencia FROM terceros WHERE referencia LIKE '41258%'")
for r in cur.fetchall():
    print(f"  ID={r[0]:<5} Tercero={r[1]:<30} Desc={r[2]:<30} Ref={r[3]}")

# Contar duplicados
cur.execute("SELECT referencia, COUNT(*) FROM terceros WHERE referencia != '' GROUP BY referencia HAVING COUNT(*) > 1")
dups = cur.fetchall()
if dups:
    print(f"\n⚠️  DUPLICADOS ENCONTRADOS: {len(dups)}")
    for ref, cnt in dups:
        print(f"  Ref={ref}: {cnt} registros")
else:
    print("\n✅ NO HAY DUPLICADOS en referencias")

# Verificar (tercero, descripcion) duplicados donde referencia = ''
cur.execute("SELECT tercero, descripcion, COUNT(*) FROM terceros WHERE referencia = '' GROUP BY tercero, descripcion HAVING COUNT(*) > 1")
dups_td = cur.fetchall()
if dups_td:
    print(f"\n⚠️  DUPLICADOS (tercero,desc): {len(dups_td)}")
else:
    print("\n✅ NO HAY DUPLICADOS en (tercero, descripcion)")

conn.close()

if not dups and not dups_td:
    print("\n" + "="*70)
    print("✅ LISTO PARA MIGRACIÓN")
    print("="*70)
else:
    print("\n⚠️  RESOLVER DUPLICADOS ANTES DE MIGRACIÓN")
