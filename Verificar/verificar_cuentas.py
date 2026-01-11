#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar cuentas disponibles
"""

import psycopg2

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

def consultar_cuentas():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Ver todas las cuentas
        cursor.execute("SELECT * FROM cuentas")
        cuentas = cursor.fetchall()
        
        print("Cuentas disponibles:")
        for cuenta in cuentas:
            print(f"  • ID: {cuenta[0]}, Cuenta: '{cuenta[1]}'")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    consultar_cuentas()
