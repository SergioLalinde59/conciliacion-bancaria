import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, user='postgres', password='SLB', database='Mvtos')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'conceptos' ORDER BY ordinal_position")
print('Columnas en tabla conceptos:')
for r in cur.fetchall():
    print(f'  {r[0]} ({r[1]})')
conn.close()
