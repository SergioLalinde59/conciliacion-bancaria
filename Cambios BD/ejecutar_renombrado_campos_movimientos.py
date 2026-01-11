#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar el renombrado de columnas en la tabla movimientos
Fecha: 2025-12-30
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def ejecutar_renombrado():
    """Ejecuta el renombrado de columnas"""
    try:
        print("="*70)
        print("RENOMBRADO DE COLUMNAS EN TABLA MOVIMIENTOS")
        print("="*70)
        print(f"\nConectando a la base de datos '{DB_CONFIG['database']}'...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("✓ Conexión exitosa\n")
        
        # Verificar columnas actuales
        print("Verificando columnas actuales...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'movimientos' 
              AND column_name IN ('CurencyID', 'AccountID', 'MonedaID', 'CuentaID')
            ORDER BY column_name
        """)
        columnas_actuales = [row[0] for row in cursor.fetchall()]
        print(f"Columnas encontradas: {columnas_actuales}\n")
        
        # Verificar si ya se hizo el renombrado
        if 'MonedaID' in columnas_actuales or 'CuentaID' in columnas_actuales:
            print("⚠️ ADVERTENCIA: Parece que las columnas ya fueron renombradas.")
            print("   Columnas nuevas detectadas:", [c for c in columnas_actuales if c in ('MonedaID', 'CuentaID')])
            respuesta = input("\n¿Deseas continuar de todos modos? (si/no): ").strip().lower()
            if respuesta != 'si':
                print("\n❌ Operación cancelada")
                cursor.close()
                conn.close()
                return
        
        # Ejecutar renombrados
        print("Iniciando renombrado de columnas...\n")
        
        cambios = []
        
        # 1. Renombrar CurencyID -> MonedaID
        try:
            print("1. Renombrando CurencyID → MonedaID...")
            cursor.execute("ALTER TABLE movimientos RENAME COLUMN CurencyID TO MonedaID")
            cambios.append("CurencyID → MonedaID")
            print("   ✓ Columna renombrada")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        # 2. Renombrar AccountID -> CuentaID
        try:
            print("2. Renombrando AccountID → CuentaID...")
            cursor.execute("ALTER TABLE movimientos RENAME COLUMN AccountID TO CuentaID")
            cambios.append("AccountID → CuentaID")
            print("   ✓ Columna renombrada")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        # 3. Renombrar FK constraint para MonedaID
        try:
            print("3. Renombrando constraint fk_currency → fk_moneda...")
            cursor.execute("ALTER TABLE movimientos RENAME CONSTRAINT fk_currency TO fk_moneda")
            cambios.append("FK: fk_currency → fk_moneda")
            print("   ✓ Constraint renombrado")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        # 4. Renombrar FK constraint para CuentaID
        try:
            print("4. Renombrando constraint fk_account → fk_cuenta...")
            cursor.execute("ALTER TABLE movimientos RENAME CONSTRAINT fk_account TO fk_cuenta")
            cambios.append("FK: fk_account → fk_cuenta")
            print("   ✓ Constraint renombrado")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        if cambios:
            # Commit de cambios
            conn.commit()
            print("\n" + "="*70)
            print("CAMBIOS APLICADOS:")
            for cambio in cambios:
                print(f"  ✓ {cambio}")
            print("="*70)
            
            # Verificación final
            print("\nVerificando cambios...")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'movimientos' 
                  AND column_name IN ('MonedaID', 'CuentaID')
                ORDER BY column_name
            """)
            columnas_finales = cursor.fetchall()
            
            if columnas_finales:
                print("\n✓ Columnas nuevas confirmadas:")
                for col in columnas_finales:
                    print(f"  • {col[0]} ({col[1]})")
            
            # Verificar constraints
            cursor.execute("""
                SELECT conname 
                FROM pg_constraint 
                WHERE conrelid = 'movimientos'::regclass 
                  AND conname IN ('fk_moneda', 'fk_cuenta')
                ORDER BY conname
            """)
            constraints = [row[0] for row in cursor.fetchall()]
            
            if constraints:
                print("\n✓ Constraints nuevos confirmados:")
                for const in constraints:
                    print(f"  • {const}")
            
            print("\n✓✓✓ RENOMBRADO COMPLETADO EXITOSAMENTE ✓✓✓")
        else:
            print("\n⚠️ No se realizaron cambios")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    ejecutar_renombrado()
