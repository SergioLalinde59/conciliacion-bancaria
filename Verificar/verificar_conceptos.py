import psycopg2

conn = psycopg2.connect(host='localhost', port=5433, user='postgres', password='SLB', dbname='Mvtos')
cur = conn.cursor()

# Contar total
cur.execute('SELECT COUNT(*) FROM conceptos')
total = cur.fetchone()[0]
print(f'Total registros en tabla conceptos: {total}')

# Mostrar ejemplos
cur.execute('SELECT claveconcepto, concepto, grupo FROM conceptos ORDER BY conceptoid LIMIT 10')
print('\nPrimeros 10 registros:')
for row in cur.fetchall():
    print(f'  {row[0]:35} | {row[1]:25} | {row[2]}')

# Verificar duplicados
cur.execute('SELECT concepto, COUNT(*) as cnt FROM conceptos GROUP BY concepto HAVING COUNT(*) > 1')
duplicados = cur.fetchall()
if duplicados:
    print(f'\n⚠️ Conceptos duplicados: {len(duplicados)}')
    for concepto, count in duplicados:
        print(f'  {concepto}: {count} veces')
else:
    print('\n✓ No hay conceptos duplicados')

cur.close()
conn.close()
