#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cargador de Datos Maestros a PostgreSQL
Carga datos desde archivos CSV a la base de datos mvtos en PostgreSQL.
Versión con interfaz gráfica (GUI).
"""

import os
import sys
import psycopg2
import pandas as pd
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from pathlib import Path
from datetime import datetime
import threading
import subprocess


class MaestrosLoaderGUI:
    """Clase para cargar datos maestros desde CSV a PostgreSQL con GUI"""
    
    # Definición de tablas y su orden de carga
    TABLES_INFO = [
        {'name': 'Cuentas', 'csv': 'Cuentas.csv', 'depends': []},
        {'name': 'Terceros', 'csv': 'Terceros.csv', 'depends': []},
        {'name': 'Monedas', 'csv': 'Monedas.csv', 'depends': []},
        {'name': 'TipoMov', 'csv': 'TipoMov.csv', 'depends': []},
        {'name': 'Grupos', 'csv': 'Grupos.csv', 'depends': []},
        {'name': 'Conceptos', 'csv': 'Conceptos.csv', 'depends': ['Grupos']},  # FK a Grupos
        {'name': 'TerceroDescripciones', 'csv': 'TerceroDescripciones.csv', 'depends': ['Terceros']},  # FK a Terceros
        {'name': 'ConfigFiltros', 'csv': 'ConfigFiltros.csv', 'depends': ['Grupos']},  # FK a Grupos
        {'name': 'ReglasAuto', 'csv': 'ReglasAuto.csv', 'depends': ['Terceros', 'Grupos', 'Conceptos']},  # FK a Terceros, Grupos, Conceptos
    ]
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cargador de Datos Maestros a PostgreSQL")
        self.root.geometry("850x700")
        self.root.resizable(True, True)
        
        # Variables de conexión
        self.host = 'localhost'
        self.port = 5433
        self.user = 'postgres'
        self.password = 'SLB'
        self.database = 'Mvtos'
        
        # Variables de control
        self.conn = None
        self.cursor = None
        self.csv_dir = Path(__file__).parent.parent / 'RecursosCompartidos' / 'Maestros'
        self.is_processing = False
        
        # Variables para checkboxes
        self.table_vars = {}
        self.reset_tables_var = tk.BooleanVar(value=False)  # Por defecto NO resetear
        
        # Variables para validación de tablas
        self.missing_tables = []
        self.create_tables_button = None
        self.validation_label = None
        
        self.setup_ui()
        
        # Validar existencia de tablas al inicio
        self.validate_tables_exist()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Cargador de Datos Maestros", 
                                font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Frame de conexión
        conn_frame = ttk.LabelFrame(main_frame, text="Configuración de Conexión", padding="10")
        conn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        conn_frame.columnconfigure(1, weight=1)
        
        ttk.Label(conn_frame, text=f"Base de datos: {self.database} @ {self.host}:{self.port}",
                  foreground="gray").grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Frame de selección de tablas
        tables_frame = ttk.LabelFrame(main_frame, text="Seleccionar Tablas a Cargar", padding="10")
        tables_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Botones seleccionar todo / ninguno
        btn_frame = ttk.Frame(tables_frame)
        btn_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Button(btn_frame, text="Seleccionar Todas", 
                   command=self.select_all_tables).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Deseleccionar Todas", 
                   command=self.deselect_all_tables).pack(side=tk.LEFT, padx=5)
        
        # Checkboxes para cada tabla
        row = 1
        col = 0
        for table_info in self.TABLES_INFO:
            var = tk.BooleanVar(value=True)
            self.table_vars[table_info['name']] = var
            
            cb = ttk.Checkbutton(tables_frame, text=table_info['name'], variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
            
            # Mostrar dependencias si las hay
            if table_info['depends']:
                dep_text = f"(requiere: {', '.join(table_info['depends'])})"
                ttk.Label(tables_frame, text=dep_text, foreground="gray", 
                          font=("Arial", 8)).grid(row=row, column=col+1, sticky=tk.W, padx=5)
            
            col += 2
            if col >= 4:  # 2 columnas
                col = 0
                row += 1
        
        # Opción de reiniciar tablas
        ttk.Separator(tables_frame, orient='horizontal').grid(
            row=row+1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        reset_cb = ttk.Checkbutton(
            tables_frame, 
            text="Limpiar tablas antes de cargar (TRUNCATE)",
            variable=self.reset_tables_var
        )
        reset_cb.grid(row=row+2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        
        reset_help = ttk.Label(
            tables_frame,
            text="Si está desmarcado, se mantendrán los datos existentes sin limpiar",
            font=("Arial", 8),
            foreground="gray"
        )
        reset_help.grid(row=row+3, column=0, columnspan=4, sticky=tk.W, padx=10)
        
        # Frame de validación de tablas
        validation_frame = ttk.LabelFrame(main_frame, text="Estado de Tablas", padding="10")
        validation_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Label para mostrar estado de validación
        self.validation_label = ttk.Label(
            validation_frame, 
            text="Verificando tablas...",
            font=("Arial", 9)
        )
        self.validation_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Botón para crear tablas (inicialmente oculto)
        self.create_tables_button = ttk.Button(
            validation_frame, 
            text="🔧 Crear Tablas Faltantes",
            command=self.launch_crear_tablas
        )
        # No lo mostramos aún, se mostrará solo si faltan tablas
        
        # Botón de carga
        self.load_button = ttk.Button(main_frame, text="Cargar Datos Seleccionados", 
                                       command=self.start_loading)
        self.load_button.grid(row=4, column=0, pady=15)
        
        # Área de log
        log_frame = ttk.LabelFrame(main_frame, text="Registro de Actividad", padding="5")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=90, 
                                                   wrap=tk.WORD, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar tags para colores
        self.log_text.tag_config('ERROR', foreground='red')
        self.log_text.tag_config('SUCCESS', foreground='green')
        self.log_text.tag_config('INFO', foreground='blue')
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Texto de estado
        self.status_label = ttk.Label(main_frame, text="Listo para comenzar", 
                                      foreground="green")
        self.status_label.grid(row=7, column=0, pady=5)
        
    def select_all_tables(self):
        """Selecciona todas las tablas"""
        for var in self.table_vars.values():
            var.set(True)
            
    def deselect_all_tables(self):
        """Deselecciona todas las tablas"""
        for var in self.table_vars.values():
            var.set(False)
    
    def validate_tables_exist(self):
        """Valida si todas las tablas necesarias existen en la base de datos"""
        try:
            # Conectar temporalmente para verificar
            temp_conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            temp_cursor = temp_conn.cursor()
            
            # Verificar cada tabla
            self.missing_tables = []
            
            # Mapeo de nombres GUI a nombres reales de PostgreSQL
            table_names_sql = {
                'Cuentas': 'cuentas',
                'Terceros': 'terceros',
                'Monedas': 'monedas',
                'TipoMov': 'tipomov',
                'Grupos': 'grupos',
                'Conceptos': 'conceptos',
                'TerceroDescripciones': 'tercero_descripciones',
                'ConfigFiltros': 'config_filtros_grupos',
                'ReglasAuto': 'reglas_clasificacion'
            }
            
            for table_info in self.TABLES_INFO:
                # Usar el mapeo para obtener el nombre real de la tabla en PostgreSQL
                table_name = table_names_sql.get(table_info['name'], table_info['name'].lower())
                query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """
                temp_cursor.execute(query, (table_name,))
                exists = temp_cursor.fetchone()[0]
                
                if not exists:
                    self.missing_tables.append(table_info['name'])
            
            temp_cursor.close()
            temp_conn.close()
            
            # Actualizar UI según el resultado
            if self.missing_tables:
                missing_str = ", ".join(self.missing_tables)
                self.validation_label.config(
                    text=f"⚠️ Tablas faltantes: {missing_str}",
                    foreground="orange"
                )
                # Mostrar botón para crear tablas
                self.create_tables_button.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
                # Deshabilitar botón de carga
                self.load_button.config(state='disabled')
                self.log(f"⚠️ Faltan {len(self.missing_tables)} tabla(s): {missing_str}", 'ERROR')
                self.log("   Haga clic en 'Crear Tablas Faltantes' para crearlas.", 'INFO')
            else:
                self.validation_label.config(
                    text="✓ Todas las tablas existen en la base de datos",
                    foreground="green"
                )
                # Ocultar botón de crear tablas si está visible
                self.create_tables_button.grid_remove()
                self.log("✓ Todas las tablas necesarias están disponibles", 'SUCCESS')
                
        except Exception as e:
            self.validation_label.config(
                text=f"✗ Error al validar tablas: {str(e)}",
                foreground="red"
            )
            self.log(f"✗ Error al conectar para validación: {str(e)}", 'ERROR')
            # Deshabilitar botón de carga por seguridad
            self.load_button.config(state='disabled')
    
    def launch_crear_tablas(self):
        """Lanza el script crear_tablas.py"""
        try:
            script_path = Path(__file__).parent / 'crear_tablas.py'
            
            if not script_path.exists():
                messagebox.showerror(
                    "Error",
                    f"No se encontró el script crear_tablas.py en:\n{script_path}"
                )
                return
            
            self.log("Lanzando crear_tablas.py...", 'INFO')
            
            # Lanzar el script en un proceso separado
            if sys.platform == 'win32':
                # En Windows, usar pythonw.exe si está disponible para no mostrar consola extra
                subprocess.Popen([sys.executable, str(script_path)], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, str(script_path)])
            
            messagebox.showinfo(
                "Script Lanzado",
                "Se ha abierto crear_tablas.py.\n\n"
                "Por favor, cree las tablas faltantes y luego cierre y vuelva a abrir esta aplicación."
            )
            
            # Sugerir al usuario que vuelva a validar después
            self.log("✓ Script crear_tablas.py lanzado correctamente", 'SUCCESS')
            self.log("   Después de crear las tablas, cierre y vuelva a abrir esta aplicación.", 'INFO')
            
        except Exception as e:
            self.log(f"✗ Error al lanzar crear_tablas.py: {str(e)}", 'ERROR')
            messagebox.showerror(
                "Error",
                f"No se pudo lanzar crear_tablas.py:\n{str(e)}"
            )
            
    def log(self, message, level='INFO'):
        """Agrega un mensaje al log con color según el nivel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        
        # Determinar tag según nivel
        if 'Error' in message or '✗' in message or level == 'ERROR':
            tag = 'ERROR'
        elif '✓' in message or 'exitosa' in message.lower():
            tag = 'SUCCESS'
        else:
            tag = 'INFO'
            
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
        
    def update_status(self, message, color="black"):
        """Actualiza el texto de estado"""
        self.status_label.config(text=message, foreground=color)
        self.root.update_idletasks()
        
    def connect(self):
        """Conecta a la base de datos PostgreSQL"""
        try:
            self.log(f"Conectando a PostgreSQL en {self.host}:{self.port}...")
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.conn.cursor()
            self.log("✓ Conexión exitosa")
            return True
        except Exception as e:
            self.log(f"✗ Error al conectar: {str(e)}", 'ERROR')
            return False
            
    def disconnect(self):
        """Cierra la conexión a la base de datos"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.log("Conexión cerrada")
        
    def check_table_exists(self, table_name):
        """Verifica si una tabla existe en la base de datos"""
        try:
            # Mapeo de nombres GUI a nombres reales de PostgreSQL
            table_names_sql = {
                'Cuentas': 'cuentas',
                'Terceros': 'terceros',
                'Monedas': 'monedas',
                'TipoMov': 'tipomov',
                'Grupos': 'grupos',
                'Conceptos': 'conceptos',
                'TerceroDescripciones': 'tercero_descripciones',
                'ConfigFiltros': 'config_filtros_grupos',
                'ReglasAuto': 'reglas_clasificacion'
            }
            
            # Obtener nombre real de la tabla
            sql_name = table_names_sql.get(table_name, table_name.lower())
            
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (sql_name,))
            
            exists = self.cursor.fetchone()[0]
            return exists
        except Exception as e:
            self.log(f"Error al verificar tabla {table_name}: {str(e)}", 'ERROR')
            return False
            
    def check_existing_tables(self, selected_tables):
        """Verifica qué tablas ya existen en la base de datos"""
        existing_tables = []
        
        for table_name in selected_tables:
            if self.check_table_exists(table_name):
                existing_tables.append(table_name)
                
        return existing_tables
        
    def create_table(self, table_name, existed_before=False, reset_mode=False):
        """Limpia una tabla específica usando TRUNCATE
        
        Args:
            table_name: Nombre de la tabla a limpiar
            existed_before: Si la tabla existía antes
            reset_mode: Si True, hace TRUNCATE de la tabla
        """
        # Nombres de tablas en minúsculas para SQL
        table_names_sql = {
            'Cuentas': 'cuentas',
            'Terceros': 'terceros',
            'Monedas': 'monedas',
            'TipoMov': 'tipomov',
            'Grupos': 'grupos',
            'Conceptos': 'conceptos',
            'TerceroDescripciones': 'tercero_descripciones',
            'ConfigFiltros': 'config_filtros_grupos',
            'ReglasAuto': 'reglas_clasificacion'
        }
        
        table_sql_name = table_names_sql.get(table_name)
        
        if not existed_before:
            # La tabla no existe, mostrar error
            self.log(f"✗ Tabla {table_name} no existe. Por favor, ejecute crear_tablas.py primero.", 'ERROR')
            return False
        
        if reset_mode:
            # La tabla existe y queremos limpiarla
            self.log(f"⚠️ Limpiando tabla {table_name}...")
            try:
                # TRUNCATE limpia todos los datos pero mantiene la estructura
                # CASCADE permite limpiar incluso si hay dependencias
                # RESTART IDENTITY reinicia los contadores SERIAL
                self.cursor.execute(f"TRUNCATE TABLE {table_sql_name} RESTART IDENTITY CASCADE;")
                self.conn.commit()
                self.log(f"✓ Tabla {table_name} limpiada correctamente")
                return True
            except Exception as e:
                self.conn.rollback()
                self.log(f"✗ Error al limpiar tabla {table_name}: {str(e)}", 'ERROR')
                return False
        else:
            # La tabla existe y no queremos limpiarla
            self.log(f"ℹ️ Tabla {table_name} ya existe con datos, se mantendrá...")
            return True
            
    def load_cuentas(self):
        """Carga datos desde Cuentas.csv"""
        csv_path = self.csv_dir / 'Cuentas.csv'
        try:
            df = pd.read_csv(csv_path)
            count = 0
            for _, row in df.iterrows():
                self.cursor.execute(
                    "INSERT INTO cuentas (cuenta) VALUES (%s) ON CONFLICT (cuenta) DO NOTHING",
                    (row['Nombre'],)  # CSV usa 'Nombre' en lugar de 'Account'
                )
                count += 1
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
            
    def load_terceros(self):
        """Carga datos desde Terceros.csv"""
        csv_path = self.csv_dir / 'Terceros.csv'
        try:
            df = pd.read_csv(csv_path)
            count = 0
            for _, row in df.iterrows():
                nombre = row['Nombre']
                if pd.isna(nombre) or str(nombre).strip() == '':
                    continue
                self.cursor.execute(
                    "INSERT INTO terceros (tercero) VALUES (%s) ON CONFLICT (tercero) DO NOTHING",
                    (nombre,)  # CSV usa 'Nombre' en lugar de 'Tercero'
                )
                count += 1
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
            
    def load_monedas(self):
        """Carga datos desde Monedas.csv"""
        csv_path = self.csv_dir / 'Monedas.csv'
        try:
            df = pd.read_csv(csv_path)
            count = 0
            for _, row in df.iterrows():
                self.cursor.execute(
                    "INSERT INTO monedas (isocode, moneda) VALUES (%s, %s) ON CONFLICT (moneda) DO NOTHING",
                    (row['Código ISO'], row['Nombre'])  # CSV usa 'Código ISO' y 'Nombre'
                )
                count += 1
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
            
    def load_tipomov(self):
        """Carga datos desde TipoMov.csv"""
        csv_path = self.csv_dir / 'TipoMov.csv'
        try:
            df = pd.read_csv(csv_path)
            count = 0
            for _, row in df.iterrows():
                self.cursor.execute(
                    "INSERT INTO tipomov (tipomov) VALUES (%s) ON CONFLICT (tipomov) DO NOTHING",
                    (row['Nombre'],)  # CSV usa 'Nombre' en lugar de 'TipoMov'
                )
                count += 1
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
            
    def load_grupos(self):
        """Carga datos desde Grupos.csv"""
        csv_path = self.csv_dir / 'Grupos.csv'
        try:
            df = pd.read_csv(csv_path)
            count = 0
            for _, row in df.iterrows():
                self.cursor.execute(
                    "INSERT INTO grupos (grupo) VALUES (%s) ON CONFLICT (grupo) DO NOTHING",
                    (row['Nombre'],)  # CSV usa 'Nombre' en lugar de 'Grupo'
                )
                count += 1
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
            
    def load_conceptos(self):
        """Carga datos desde Conceptos.csv"""
        csv_path = self.csv_dir / 'Conceptos.csv'
        grupos_csv_path = self.csv_dir / 'Grupos.csv'
        
        try:
            # 1. Cargar mapeo de ID a Nombre de Grupo desde Grupos.csv
            # Se asume que el ID en Conceptos.csv corresponde al índice (base 1) en Grupos.csv
            grupos_map = []
            if grupos_csv_path.exists():
                df_grupos = pd.read_csv(grupos_csv_path)
                for _, row in df_grupos.iterrows():
                    grupos_map.append(row['Nombre'])
            
            df = pd.read_csv(csv_path)
            count = 0
            
            # Cache para evitar consultas repetitivas a la BD
            grupo_db_id_cache = {}
            
            for _, row in df.iterrows():
                concepto = row['Concepto']
                if pd.isna(concepto) or str(concepto).strip() == '':
                    continue
                    
                # Buscar el grupoid usando el Grupo ID del CSV
                grupoid_fk = None
                grupo_id_csv = row.get('Grupo ID', None)
                
                if not pd.isna(grupo_id_csv):
                    try:
                        # Convertir a cero-based index
                        idx = int(grupo_id_csv) - 1
                        if 0 <= idx < len(grupos_map):
                            grupo_nombre = grupos_map[idx]
                            
                            # Buscar ID real en BD (usando caché)
                            if grupo_nombre in grupo_db_id_cache:
                                grupoid_fk = grupo_db_id_cache[grupo_nombre]
                            else:
                                self.cursor.execute(
                                    "SELECT grupoid FROM grupos WHERE grupo = %s LIMIT 1",
                                    (grupo_nombre,)
                                )
                                result = self.cursor.fetchone()
                                if result:
                                    grupoid_fk = result[0]
                                    grupo_db_id_cache[grupo_nombre] = grupoid_fk
                                else:
                                    self.log(f"⚠️ Grupo '{grupo_nombre}' (ID CSV: {grupo_id_csv}) no encontrado en BD", 'WARNING')
                        else:
                            self.log(f"⚠️ Índice de grupo fuera de rango: {grupo_id_csv}", 'WARNING')
                    except ValueError:
                        self.log(f"⚠️ ID de grupo inválido: {grupo_id_csv}", 'WARNING')
                
                if grupoid_fk is not None:
                    self.cursor.execute(
                        """INSERT INTO conceptos 
                        (concepto, grupoid_fk)
                        VALUES (%s, %s)
                        ON CONFLICT (grupoid_fk, concepto) DO NOTHING""",
                        (concepto, grupoid_fk)
                    )
                    count += self.cursor.rowcount
                
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def load_tercerodescripciones(self):
        """Carga datos desde TerceroDescripciones.csv"""
        csv_path = self.csv_dir / 'TerceroDescripciones.csv'
        try:
            df = pd.read_csv(csv_path)
            count = 0
            for _, row in df.iterrows():
                # Buscar el terceroid usando el nombre del tercero
                terceroid_fk = None
                if not pd.isna(row.get('Tercero', None)):
                    self.cursor.execute(
                        "SELECT terceroid FROM terceros WHERE tercero = %s LIMIT 1",
                        (row['Tercero'],)
                    )
                    result = self.cursor.fetchone()
                    if result:
                        terceroid_fk = result[0]
                
                if terceroid_fk is None:
                    # Si no encontramos el tercero, intentar con TerceroID directo (varias opciones de casing)
                    terceroid_fk = row.get('TerceroID', row.get('terceroid', None))
                    if pd.isna(terceroid_fk):
                        continue  # Saltamos si no hay tercero válido
                
                # Manejar descripción con y sin tilde due to CSV variations
                descripcion = row.get('Descripcion', row.get('Descripción', '')) 
                if pd.isna(descripcion):
                    descripcion = ''
                    
                referencia = row.get('Referencia', '') if not pd.isna(row.get('Referencia', None)) else ''
                activa = row.get('Activa', True) if not pd.isna(row.get('Activa', None)) else True
                
                self.cursor.execute(
                    """INSERT INTO tercero_descripciones 
                    (terceroid, descripcion, referencia, activa)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING""",
                    (terceroid_fk, descripcion, referencia, activa)
                )
                count += self.cursor.rowcount
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def load_configfiltros(self):
        """Carga datos desde ConfigFiltros.csv"""
        csv_path = self.csv_dir / 'ConfigFiltros.csv'
        try:
            df = pd.read_csv(csv_path)
            count = 0
            for _, row in df.iterrows():
                # Buscar el grupoid usando el nombre del grupo
                grupoid_fk = None
                if not pd.isna(row.get('Grupo', None)):
                    self.cursor.execute(
                        "SELECT grupoid FROM grupos WHERE grupo = %s LIMIT 1",
                        (row['Grupo'],)
                    )
                    result = self.cursor.fetchone()
                    if result:
                        grupoid_fk = result[0]
                
                if grupoid_fk is None:
                    # Si no encontramos el grupo, intentar con GrupoID directo
                    grupoid_fk = row.get('GrupoID', None)
                    if pd.isna(grupoid_fk):
                        continue  # Saltamos si no hay grupo válido
                
                etiqueta = row.get('Etiqueta', '') if not pd.isna(row.get('Etiqueta', None)) else ''
                activo_por_defecto = row.get('ActivoPorDefecto', True) if not pd.isna(row.get('ActivoPorDefecto', None)) else True
                
                self.cursor.execute(
                    """INSERT INTO config_filtros_grupos 
                    (grupo_id, etiqueta, activo_por_defecto)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (grupo_id) DO UPDATE SET 
                        etiqueta = EXCLUDED.etiqueta,
                        activo_por_defecto = EXCLUDED.activo_por_defecto""",
                    (grupoid_fk, etiqueta, activo_por_defecto)
                )
                count += self.cursor.rowcount
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def load_reglasauto(self):
        """Carga datos desde ReglasAuto.csv"""
        csv_path = self.csv_dir / 'ReglasAuto.csv'
        try:
            df = pd.read_csv(csv_path)
            count = 0
            for _, row in df.iterrows():
                patron = row.get('Patron', '') if not pd.isna(row.get('Patron', None)) else ''
                if not patron:
                    continue  # Patrón es requerido
                
                # Buscar tercero_id
                tercero_id = None
                if not pd.isna(row.get('Tercero', None)):
                    self.cursor.execute(
                        "SELECT terceroid FROM terceros WHERE tercero = %s LIMIT 1",
                        (row['Tercero'],)
                    )
                    result = self.cursor.fetchone()
                    if result:
                        tercero_id = result[0]
                elif not pd.isna(row.get('TerceroID', None)):
                    tercero_id = int(row['TerceroID'])
                
                # Buscar grupo_id
                grupo_id = None
                if not pd.isna(row.get('Grupo', None)):
                    self.cursor.execute(
                        "SELECT grupoid FROM grupos WHERE grupo = %s LIMIT 1",
                        (row['Grupo'],)
                    )
                    result = self.cursor.fetchone()
                    if result:
                        grupo_id = result[0]
                elif not pd.isna(row.get('GrupoID', None)):
                    grupo_id = int(row['GrupoID'])
                
                # Buscar concepto_id
                concepto_id = None
                if not pd.isna(row.get('Concepto', None)):
                    self.cursor.execute(
                        "SELECT conceptoid FROM conceptos WHERE concepto = %s LIMIT 1",
                        (row['Concepto'],)
                    )
                    result = self.cursor.fetchone()
                    if result:
                        concepto_id = result[0]
                elif not pd.isna(row.get('ConceptoID', None)):
                    concepto_id = int(row['ConceptoID'])
                
                tipo_match = row.get('TipoMatch', 'contains') if not pd.isna(row.get('TipoMatch', None)) else 'contains'
                
                self.cursor.execute(
                    """INSERT INTO reglas_clasificacion 
                    (patron, tercero_id, grupo_id, concepto_id, tipo_match)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (patron, tercero_id, grupo_id, concepto_id, tipo_match)
                )
                count += self.cursor.rowcount
            self.conn.commit()
            return count
        except Exception as e:
            self.conn.rollback()
            raise e
            
    def check_table_has_data(self, table_name):
        """Verifica si una tabla tiene datos"""
        try:
            # Mapeo de nombres GUI a nombres reales de PostgreSQL
            table_names_sql = {
                'Cuentas': 'cuentas',
                'Terceros': 'terceros',
                'Monedas': 'monedas',
                'TipoMov': 'tipomov',
                'Grupos': 'grupos',
                'Conceptos': 'conceptos',
                'TerceroDescripciones': 'tercero_descripciones',
                'ConfigFiltros': 'config_filtros_grupos',
                'ReglasAuto': 'reglas_clasificacion'
            }
            
            sql_name = table_names_sql.get(table_name, table_name.lower())
            
            # Usar una conexión temporal si no hay una activa
            conn_local = None
            cursor_local = None
            
            if self.cursor:
                cursor_local = self.cursor
            else:
                conn_local = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
                cursor_local = conn_local.cursor()
                
            cursor_local.execute(f"SELECT COUNT(*) FROM {sql_name}")
            count = cursor_local.fetchone()[0]
            
            if conn_local:
                cursor_local.close()
                conn_local.close()
                
            return count > 0
            
        except Exception:
            return False

    def start_loading(self):
        """Inicia el proceso de carga en un hilo separado"""
        if self.is_processing:
            messagebox.showwarning("Advertencia", "Ya hay un proceso de carga en ejecución.")
            return
            
        # Verificar que al menos una tabla esté seleccionada
        selected_tables = [name for name, var in self.table_vars.items() if var.get()]
        if not selected_tables:
            messagebox.showerror("Error", "Debes seleccionar al menos una tabla para cargar.")
            return
            
        # Verificar dependencias
        for table_name in selected_tables:
            table_info = next(t for t in self.TABLES_INFO if t['name'] == table_name)
            for dep in table_info['depends']:
                if dep not in selected_tables:
                    # Si la dependencia no está seleccionada, verificar si tiene datos en la BD
                    has_data = self.check_table_has_data(dep)
                    if not has_data:
                        messagebox.showerror("Error de Dependencia", 
                                            f"La tabla '{table_name}' requiere '{dep}'.\n"
                                            f"'{dep}' no está seleccionada y no tiene datos en la base de datos.")
                        return
        
        # Ejecutar en hilo separado
        self.is_processing = True
        self.load_button.config(state='disabled')
        thread = threading.Thread(target=self.load_data, args=(selected_tables,), daemon=True)
        thread.start()
        
    def load_data(self, selected_tables):
        """Carga los datos de las tablas seleccionadas"""
        try:
            self.log("="*70)
            self.log("INICIANDO CARGA DE DATOS MAESTROS")
            self.log("="*70)
            self.log(f"Tablas seleccionadas: {', '.join(selected_tables)}")
            self.log("")
            
            # Conectar
            if not self.connect():
                self.update_status("Error de conexión", "red")
                return
            
            # Obtener modo de reset
            reset_mode = self.reset_tables_var.get()
            
            if reset_mode:
                self.log("⚠️ MODO: Limpiar tablas antes de cargar (TRUNCATE)")
            else:
                self.log("ℹ️ MODO: Mantener datos existentes (sin TRUNCATE)")
            self.log("")
                
            # Verificar qué tablas ya existen
            self.log("Verificando tablas existentes en la base de datos...")
            existing_tables = self.check_existing_tables(selected_tables)
            
            if existing_tables:
                self.log(f"ℹ️ Se encontraron {len(existing_tables)} tabla(s) existente(s):", 'INFO')
                for table in existing_tables:
                    self.log(f"   - {table}", 'INFO')
                
                if reset_mode:
                    self.log("⚠️ Las tablas existentes serán LIMPIADAS (TRUNCATE).", 'INFO')
                    self.log("")
                    
                    # Mostrar advertencia al usuario
                    response = messagebox.askyesno(
                        "Tablas Existentes Detectadas",
                        f"Se encontraron {len(existing_tables)} tabla(s) que ya existen:\n\n" +
                        "\n".join([f"  • {t}" for t in existing_tables]) +
                        "\n\n⚠️ ADVERTENCIA: Estas tablas serán LIMPIADAS (TRUNCATE).\n" +
                        "Todos los datos actuales se perderán, pero la estructura se mantendrá.\n\n" +
                        "¿Deseas continuar?",
                        icon='warning'
                    )
                    
                    if not response:
                        self.log("❌ Proceso cancelado por el usuario")
                        self.disconnect()
                        self.update_status("Cancelado por el usuario", "orange")
                        return
                else:
                    self.log("✓ Las tablas existentes se mantendrán.", 'INFO')
                    self.log("")
            else:
                self.log("✓ No se encontraron tablas existentes. Se crearán nuevas tablas.")
                self.log("")
                
            # Configurar barra de progreso
            self.progress_bar['maximum'] = len(selected_tables)
            self.progress_bar['value'] = 0
            
            # Crear y cargar tablas
            totals = {}
            errors = []
            
            for idx, table_name in enumerate(selected_tables, 1):
                try:
                    self.update_status(f"Procesando {idx}/{len(selected_tables)}: {table_name}", "blue")
                    self.log(f"\n📋 Procesando tabla: {table_name}")
                    
                    # Verificar si la tabla existe
                    table_existed = self.check_table_exists(table_name)
                    
                    # Crear tabla
                    if not self.create_table(table_name, existed_before=table_existed, reset_mode=reset_mode):
                        errors.append(f"{table_name}: Error al crear tabla")
                        continue
                        
                    # Cargar datos
                    self.log(f"Cargando datos desde {table_name}.csv...")
                    load_method = getattr(self, f'load_{table_name.lower()}')
                    count = load_method()
                    totals[table_name] = count
                    self.log(f"✓ {count} registros cargados en {table_name}")
                    
                except Exception as e:
                    error_msg = f"{table_name}: {str(e)}"
                    self.log(f"✗ Error al procesar {table_name}: {str(e)}", 'ERROR')
                    errors.append(error_msg)
                    totals[table_name] = 0
                    
                self.progress_bar['value'] = idx
            
            # Resumen
            self.log("")
            self.log("="*70)
            self.log("RESUMEN DE CARGA")
            self.log("="*70)
            total_records = 0
            for table, count in totals.items():
                self.log(f"  {table:15} : {count:5} registros")
                total_records += count
            self.log("-"*70)
            self.log(f"  {'TOTAL':15} : {total_records:5} registros")
            self.log("="*70)
            
            if errors:
                self.log(f"\n⚠️ Se encontraron {len(errors)} error(es):", 'ERROR')
                for error in errors:
                    self.log(f"   - {error}", 'ERROR')
            
            # Desconectar
            self.disconnect()
            
            # Mensaje final
            if errors:
                self.update_status("Completado con errores", "orange")
                messagebox.showwarning("Completado con errores",
                                      f"Se cargaron {total_records} registros.\n"
                                      f"Se encontraron {len(errors)} error(es).\n"
                                      f"Revisa el registro para más detalles.")
            else:
                self.update_status("Completado exitosamente", "green")
                self.log("\n✓ PROCESO COMPLETADO EXITOSAMENTE")
                messagebox.showinfo("Éxito",
                                   f"¡Proceso completado!\n\n"
                                   f"Total de registros cargados: {total_records}")
                                   
        except Exception as e:
            self.log(f"\n✗ Error crítico: {str(e)}", 'ERROR')
            self.update_status("Error crítico", "red")
            messagebox.showerror("Error", f"Error crítico:\n{str(e)}")
            
        finally:
            self.is_processing = False
            self.load_button.config(state='normal')
            self.progress_bar['value'] = 0


def main():
    """Función principal"""
    root = tk.Tk()
    app = MaestrosLoaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
