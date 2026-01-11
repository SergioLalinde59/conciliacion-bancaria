#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creador de Tablas para Base de Datos PostgreSQL
Crea las tablas maestras en la base de datos mvtos.
Versión con interfaz gráfica (GUI).
"""

import os
import sys
import psycopg2
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from pathlib import Path
from datetime import datetime
import threading


class TablesCreatorGUI:
    """Clase para crear tablas maestras en PostgreSQL con GUI"""
    
    # Información de las tablas
    TABLES_INFO = [
        {'name': 'Cuentas', 'depends': []},
        {'name': 'Terceros', 'depends': []},
        {'name': 'Monedas', 'depends': []},
        {'name': 'TipoMov', 'depends': []},
        {'name': 'Grupos', 'depends': []},
        {'name': 'Conceptos', 'depends': ['Grupos']},  # Depende de Grupos
        {'name': 'TerceroDescripciones', 'depends': ['Terceros']},
        {'name': 'ConfigFiltros', 'depends': ['Grupos']},
        {'name': 'ReglasAuto', 'depends': ['Terceros', 'Grupos', 'Conceptos']}
    ]
    
    def __init__(self, root):
        self.root = root
        self.root.title("Creador de Tablas Maestras - PostgreSQL")
        self.root.geometry("800x600")
        
        # Configuración de la conexión
        self.db_config = {
            'host': 'localhost',
            'port': '5433',
            'database': 'Mvtos',
            'user': 'postgres',
            'password': 'SLB'
        }
        
        self.conn = None
        self.cursor = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Creador de Tablas Maestras",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Frame de configuración de BD
        config_frame = ttk.LabelFrame(main_frame, text="Configuración de Base de Datos", padding="5")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(config_frame, text=f"Host: {self.db_config['host']}").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(config_frame, text=f"Puerto: {self.db_config['port']}").grid(row=0, column=1, sticky=tk.W)
        ttk.Label(config_frame, text=f"Base de Datos: {self.db_config['database']}").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(config_frame, text=f"Usuario: {self.db_config['user']}").grid(row=1, column=1, sticky=tk.W)
        
        # Frame de selección de tablas
        tables_frame = ttk.LabelFrame(main_frame, text="Seleccione las tablas a crear", padding="5")
        tables_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Checkboxes para las tablas
        self.table_vars = {}
        for i, table_info in enumerate(self.TABLES_INFO):
            table_name = table_info['name']
            var = tk.BooleanVar(value=False)
            self.table_vars[table_name] = var
            cb = ttk.Checkbutton(tables_frame, text=table_name, variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Botones de selección
        button_frame = ttk.Frame(tables_frame)
        button_frame.grid(row=len(self.TABLES_INFO), column=0, pady=5)
        
        ttk.Button(button_frame, text="Seleccionar Todas", command=self.select_all_tables).grid(row=0, column=0, padx=2)
        ttk.Button(button_frame, text="Deseleccionar Todas", command=self.deselect_all_tables).grid(row=0, column=1, padx=2)
        
        # Frame de log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Área de texto para el log
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=50,
            height=20,
            state='disabled'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configurar colores para el log
        self.log_text.tag_config('INFO', foreground='black')
        self.log_text.tag_config('SUCCESS', foreground='green')
        self.log_text.tag_config('WARNING', foreground='orange')
        self.log_text.tag_config('ERROR', foreground='red')
        
        # Frame de estado y botones
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Etiqueta de estado
        self.status_label = ttk.Label(bottom_frame, text="Listo", foreground="black")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(bottom_frame, mode='determinate', length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Botón de crear
        self.create_button = ttk.Button(
            bottom_frame,
            text="Crear Tablas",
            command=self.start_creation
        )
        self.create_button.pack(side=tk.RIGHT, padx=5)
    
    def select_all_tables(self):
        """Selecciona todas las tablas"""
        for var in self.table_vars.values():
            var.set(True)
    
    def deselect_all_tables(self):
        """Deselecciona todas las tablas"""
        for var in self.table_vars.values():
            var.set(False)
    
    def log(self, message, level='INFO'):
        """Agrega un mensaje al log con color según el nivel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, formatted_message, level)
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
            self.log("Conectando a la base de datos...")
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            self.cursor = self.conn.cursor()
            self.log("✓ Conexión exitosa", 'SUCCESS')
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
        self.log("Conexión cerrada", 'INFO')
    
    def check_table_exists(self, table_name):
        """Verifica si una tabla existe en la base de datos"""
        try:
            # Mapeo manual para nombres que no son directos
            table_map = {
                'TerceroDescripciones': 'tercero_descripciones',
                'ConfigFiltros': 'config_filtros_grupos',
                'ReglasAuto': 'reglas_clasificacion'
            }
            
            # Usar mapeo o minúsculas por defecto
            sql_name = table_map.get(table_name, table_name.lower())
            
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """
            self.cursor.execute(query, (sql_name,))
            exists = self.cursor.fetchone()[0]
            return exists
        except Exception as e:
            self.log(f"✗ Error al verificar tabla {table_name}: {str(e)}", 'ERROR')
            return False
    
    def create_table(self, table_name):
        """Crea una tabla específica
        
        Args:
            table_name: Nombre de la tabla a crear
        
        Returns:
            bool: True si la tabla fue creada exitosamente, False en caso contrario
        """
        # SQL para CREATE de cada tabla
        table_sql = {
            'Cuentas': """
                CREATE TABLE cuentas (
                    cuentaid SERIAL PRIMARY KEY,
                    cuenta VARCHAR(50) NOT NULL,
                    
                    UNIQUE (cuenta)
                );
            """,
            'Terceros': """
                CREATE TABLE terceros (
                    terceroid SERIAL PRIMARY KEY,
                    tercero VARCHAR(50) NOT NULL,
                    activa BOOLEAN DEFAULT TRUE,
                    
                    UNIQUE (tercero)
                );
            """,
            'Monedas': """
                CREATE TABLE monedas (
                    monedaid SERIAL PRIMARY KEY,
                    isocode VARCHAR(50) NOT NULL,
                    moneda VARCHAR(50) NOT NULL,
                    
                    UNIQUE (moneda)
                );
            """,
            'TipoMov': """
                CREATE TABLE tipomov (
                    tipomovid SERIAL PRIMARY KEY,
                    tipomov VARCHAR(50) NOT NULL,
                    
                    UNIQUE (tipomov)
                );
            """,
            'Grupos': """
                CREATE TABLE grupos (
                    grupoid SERIAL PRIMARY KEY,
                    grupo VARCHAR(50) NOT NULL,
                    
                    UNIQUE (grupo)
                );
            """,
            'Conceptos': """
                CREATE TABLE conceptos (
                    conceptoid SERIAL PRIMARY KEY,
                    concepto VARCHAR(100) NOT NULL,
                    grupoid_fk INTEGER,
                    activa BOOLEAN DEFAULT TRUE,
                    
                    UNIQUE (grupoid_fk, concepto),
                    FOREIGN KEY (grupoid_fk) REFERENCES grupos(grupoid)
                );
            """,
            'TerceroDescripciones': """
                CREATE TABLE tercero_descripciones (
                    tercerodescripcionid SERIAL PRIMARY KEY,
                    terceroid INTEGER NOT NULL,
                    descripcion VARCHAR(255) NOT NULL,
                    referencia VARCHAR(100),
                    activa BOOLEAN DEFAULT TRUE,
                    
                    UNIQUE (terceroid, descripcion, referencia),
                    FOREIGN KEY (terceroid) REFERENCES terceros(terceroid)
                );
            """,
            'ConfigFiltros': """
                CREATE TABLE config_filtros_grupos (
                    configfiltroid SERIAL PRIMARY KEY,
                    grupo_id INTEGER NOT NULL,
                    etiqueta VARCHAR(100),
                    activo_por_defecto BOOLEAN DEFAULT TRUE,
                    
                    UNIQUE (grupo_id),
                    FOREIGN KEY (grupo_id) REFERENCES grupos(grupoid)
                );
            """,
            'ReglasAuto': """
                CREATE TABLE reglas_clasificacion (
                    reglaid SERIAL PRIMARY KEY,
                    patron VARCHAR(255) NOT NULL,
                    tercero_id INTEGER,
                    grupo_id INTEGER,
                    concepto_id INTEGER,
                    tipo_match VARCHAR(20) DEFAULT 'contains',
                    
                    FOREIGN KEY (tercero_id) REFERENCES terceros(terceroid),
                    FOREIGN KEY (grupo_id) REFERENCES grupos(grupoid),
                    FOREIGN KEY (concepto_id) REFERENCES conceptos(conceptoid)
                );
            """
        }
        
        # Verificar si la tabla ya existe
        table_sql_name = table_name.lower()
        if self.check_table_exists(table_sql_name):
            self.log(f"⚠️ Tabla {table_name} ya existe, omitiendo...", 'WARNING')
            return True
        
        try:
            self.log(f"Creando tabla {table_name}...")
            self.cursor.execute(table_sql[table_name])
            self.conn.commit()
            self.log(f"✓ Tabla {table_name} creada exitosamente", 'SUCCESS')
            return True
        except Exception as e:
            self.conn.rollback()
            self.log(f"✗ Error al crear tabla {table_name}: {str(e)}", 'ERROR')
            return False
    
    def start_creation(self):
        """Inicia el proceso de creación en un hilo separado"""
        # Obtener tablas seleccionadas
        selected_tables = [
            name for name, var in self.table_vars.items() if var.get()
        ]
        
        if not selected_tables:
            messagebox.showwarning("Advertencia", "Por favor, seleccione al menos una tabla.")
            return
        
        # Deshabilitar el botón durante la creación
        self.create_button.config(state='disabled')
        
        # Iniciar en un hilo separado para no bloquear la UI
        thread = threading.Thread(target=self.create_tables, args=(selected_tables,))
        thread.daemon = True
        thread.start()
    
    def create_tables(self, selected_tables):
        """Crea las tablas seleccionadas
        
        Args:
            selected_tables: Lista de nombres de tablas a crear
        """
        try:
            self.update_status("Procesando...", "blue")
            self.log("=" * 50)
            self.log("Iniciando creación de tablas...")
            self.log("=" * 50)
            
            # Conectar a la base de datos
            if not self.connect():
                messagebox.showerror("Error", "No se pudo conectar a la base de datos")
                return
            
            # Configurar barra de progreso
            self.progress_bar['maximum'] = len(selected_tables)
            self.progress_bar['value'] = 0
            
            # Ordenar tablas según dependencias
            ordered_tables = []
            for table_info in self.TABLES_INFO:
                if table_info['name'] in selected_tables:
                    ordered_tables.append(table_info['name'])
            
            # Crear tablas en orden
            success_count = 0
            error_count = 0
            
            for i, table_name in enumerate(ordered_tables, 1):
                self.log(f"\n({i}/{len(ordered_tables)}) Procesando {table_name}...")
                
                if self.create_table(table_name):
                    success_count += 1
                else:
                    error_count += 1
                
                # Actualizar barra de progreso
                self.progress_bar['value'] = i
                self.root.update_idletasks()
            
            # Mostrar resumen
            self.log("\n" + "=" * 50)
            self.log("RESUMEN DE CREACIÓN")
            self.log("=" * 50)
            self.log(f"Tablas creadas exitosamente: {success_count}", 'SUCCESS')
            if error_count > 0:
                self.log(f"Tablas con errores: {error_count}", 'ERROR')
            
            # Desconectar
            self.disconnect()
            
            # Actualizar estado
            if error_count == 0:
                self.update_status("✓ Proceso completado exitosamente", "green")
                messagebox.showinfo("Éxito", f"Se crearon {success_count} tabla(s) exitosamente.")
            else:
                self.update_status("⚠️ Proceso completado con errores", "orange")
                messagebox.showwarning(
                    "Advertencia",
                    f"Proceso completado con {error_count} error(es).\nRevisar el log para más detalles."
                )
            
        except Exception as e:
            self.log(f"\n✗ Error general: {str(e)}", 'ERROR')
            self.update_status("✗ Error en el proceso", "red")
            messagebox.showerror("Error", f"Error durante la creación:\n{str(e)}")
        
        finally:
            # Rehabilitar el botón
            self.create_button.config(state='normal')
            # Resetear barra de progreso
            self.progress_bar['value'] = 0


def main():
    """Función principal"""
    root = tk.Tk()
    app = TablesCreatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
