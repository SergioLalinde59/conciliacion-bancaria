
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def debug_loading():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. Fetch Groups
        cursor.execute("SELECT grupoid, grupo FROM grupos ORDER BY grupo")
        grupos = cursor.fetchall()
        print(f"Loaded {len(grupos)} groups.")
        
        grupo_9 = next((g for g in grupos if g[0] == 9), None)
        print(f"Group ID 9: {grupo_9}")
        
        # 2. Fetch Concepts
        cursor.execute("SELECT conceptoid, concepto, grupoid_fk FROM conceptos ORDER BY concepto")
        conceptos = cursor.fetchall()
        print(f"Loaded {len(conceptos)} concepts.")
        
        # 3. Check Concept 812
        concepto_812 = next((c for c in conceptos if c[0] == 812), None)
        print(f"Concept ID 812: {concepto_812}")
        
        # 4. Simulate Filtering for Group 9
        grupo_seleccionado_id = 9
        conceptos_filtrados = [(cid, nombre) for cid, nombre, gid in conceptos 
                               if gid == grupo_seleccionado_id]
        
        print(f"\nFiltered concepts for Group ID 9:")
        found = False
        for cid, nombre in conceptos_filtrados:
            print(f" - {cid}: {nombre}")
            if cid == 812:
                found = True
                
        if found:
            print("\nSUCCESS: Concept 812 found in filtered list.")
        else:
            print("\nFAILURE: Concept 812 NOT found in filtered list.")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_loading()
