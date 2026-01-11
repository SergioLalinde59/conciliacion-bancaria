#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para cargar solo la tabla conceptos
"""

import psycopg2
import pandas as pd
from pathlib import Path

# Configuración
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def main():
    print("="*70)
    print("CARGANDO TABLA CONCEPTOS")
    print("="*70)
    
    try:
        # Conectar
        print("\n1. Conectando a la base de datos...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("   ✓ Conexión exitosa")
        
        # Leer CSV
        csv_path = Path(__file__).parent.parent / 'RecursosCompartidos' / 'Maestros' / 'Conceptos.csv'
        print(f"\n2. Leyendo {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"   ✓ {len(df)} filas leídas")
        
        # Cargar datos
        print("\n3. Insertando registros...")
        count_inserted = 0
        count_skipped = 0
        
        for idx, row in df.iterrows():
            concepto = row.get('Concepto', '')
            if pd.isna(concepto) or str(concepto).strip() == '':
                count_skipped += 1
                continue
            
            # Buscar grupoid
            grupoid_fk = None
            if not pd.isna(row.get('GrupoID', None)):
                grupoid_fk = int(row['GrupoID'])
            
            # Insertar con unique en (grupoid_fk, concepto)
            cursor.execute(
                """INSERT INTO conceptos 
                (concepto, grupoid_fk)
                VALUES (%s, %s)
                ON CONFLICT (grupoid_fk, concepto) DO NOTHING""",
                (concepto, grupoid_fk)
            )
            
            # Contar solo si se insertó (rowcount > 0)
            count_inserted += cursor.rowcount
        
        # Commit
        conn.commit()
        print(f"   ✓ {count_inserted} registros insertados")
        if count_skipped > 0:
            print(f"   ℹ️ {count_skipped} registros omitidos (Concepto vacío)")
        
        # Verificar
        print("\n4. Verificando la carga...")
        cursor.execute("SELECT COUNT(*) FROM conceptos")
        total = cursor.fetchone()[0]
        print(f"   ✓ Total de registros en la tabla: {total}")
        
        # Cerrar
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✓ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"\nResumen:")
        print(f"  - Registros en CSV: {len(df)}")
        print(f"  - Registros insertados: {count_inserted}")
        print(f"  - Registros omitidos: {count_skipped}")
        print(f"  - Total en base de datos: {total}")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
