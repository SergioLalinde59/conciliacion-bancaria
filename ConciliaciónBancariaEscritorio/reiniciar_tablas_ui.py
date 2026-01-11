#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script con Interfaz Gráfica para Reiniciar Tablas del Proyecto
Permite seleccionar tablas para reiniciar (DROP + CREATE) en la base de datos Mvtos.

Autor: Antigravity
Fecha: 2025-12-29
Actualizado: 2026-01-06 - Agregadas tablas nuevas y campo Detalle
"""

import psycopg2
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

# Información de tablas con sus dependencias (orden de dependencias invertido para DROP)
TABLAS_INFO = [
    {'name': 'movimientos', 'display': 'Movimientos', 'depends_on': ['cuentas', 'terceros', 'monedas', 'grupos', 'conceptos']},
    {'name': 'tercero_descripciones', 'display': 'Tercero Descripciones', 'depends_on': ['terceros']},
    {'name': 'reglas_clasificacion', 'display': 'Reglas de Clasificación', 'depends_on': ['terceros', 'grupos', 'conceptos']},
    {'name': 'config_filtros_grupos', 'display': 'Config Filtros Grupos', 'depends_on': ['grupos']},
    {'name': 'conceptos', 'display': 'Conceptos', 'depends_on': ['grupos']},
    {'name': 'grupos', 'display': 'Grupos', 'depends_on': []},
    {'name': 'tipomov', 'display': 'Tipo de Movimiento', 'depends_on': []},
    {'name': 'monedas', 'display': 'Monedas', 'depends_on': []},
    {'name': 'terceros', 'display': 'Terceros', 'depends_on': []},
    {'name': 'cuentas', 'display': 'Cuentas', 'depends_on': []},
]

# SQL para crear cada tabla (actualizado con los campos actuales)
TABLE_CREATE_SQL = {
    'cuentas': """
        CREATE TABLE cuentas (
            cuentaid SERIAL PRIMARY KEY,
            cuenta VARCHAR(50) NOT NULL,
            activa BOOLEAN DEFAULT TRUE,
            permite_carga BOOLEAN DEFAULT TRUE,

            UNIQUE (cuenta)
        );
    """,
    'terceros': """
        CREATE TABLE terceros (
            terceroid SERIAL PRIMARY KEY,
            tercero VARCHAR(50) NOT NULL,
            activa BOOLEAN DEFAULT TRUE,

            UNIQUE (tercero)
        );
    """,
    'monedas': """
        CREATE TABLE monedas (
            monedaid SERIAL PRIMARY KEY,
            isocode VARCHAR(10) NOT NULL,
            moneda VARCHAR(50) NOT NULL,
            activa BOOLEAN DEFAULT TRUE,

            UNIQUE (moneda)
        );
    """,
    'tipomov': """
        CREATE TABLE tipomov (
            tipomovid SERIAL PRIMARY KEY,
            tipomov VARCHAR(50) NOT NULL,

            UNIQUE (tipomov)
        );
    """,
    'grupos': """
        CREATE TABLE grupos (
            grupoid SERIAL PRIMARY KEY,
            grupo VARCHAR(50) NOT NULL,
            activa BOOLEAN DEFAULT TRUE,

            UNIQUE (grupo)
        );
    """,
    'conceptos': """
        CREATE TABLE conceptos (
            conceptoid SERIAL PRIMARY KEY,
            concepto VARCHAR(100) NOT NULL,
            grupoid_fk INTEGER,
            activa BOOLEAN DEFAULT TRUE,

            UNIQUE (grupoid_fk, concepto),
            FOREIGN KEY (grupoid_fk) REFERENCES grupos(grupoid)
        );
    """,
    'movimientos': """
        CREATE TABLE movimientos (
            Id SERIAL PRIMARY KEY,
            Fecha DATE NOT NULL,
            Descripcion VARCHAR(100),
            Referencia VARCHAR(500),
            Valor DECIMAL(15, 2),
            USD DECIMAL(15, 2),
            TRM DECIMAL(10, 4),
            Detalle TEXT,
            MonedaID INTEGER,
            CuentaID INTEGER,
            TerceroID INTEGER,
            GrupoID INTEGER,
            ConceptoID INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_moneda FOREIGN KEY (MonedaID) REFERENCES Monedas(MonedaID),
            CONSTRAINT fk_cuenta FOREIGN KEY (CuentaID) REFERENCES Cuentas(CuentaID),
            CONSTRAINT fk_tercero FOREIGN KEY (TerceroID) REFERENCES Terceros(TerceroID),
            CONSTRAINT fk_grupo FOREIGN KEY (GrupoID) REFERENCES Grupos(GrupoID),
            CONSTRAINT fk_concepto FOREIGN KEY (ConceptoID) REFERENCES Conceptos(ConceptoID)
        );
    """,
    'reglas_clasificacion': """
        CREATE TABLE reglas_clasificacion (
            id SERIAL PRIMARY KEY,
            patron VARCHAR(255) NOT NULL,
            tercero_id INTEGER,
            grupo_id INTEGER,
            concepto_id INTEGER,
            tipo_match VARCHAR(50) DEFAULT 'contains',
            
            CONSTRAINT fk_regla_tercero FOREIGN KEY (tercero_id) REFERENCES Terceros(TerceroID),
            CONSTRAINT fk_regla_grupo FOREIGN KEY (grupo_id) REFERENCES Grupos(GrupoID),
            CONSTRAINT fk_regla_concepto FOREIGN KEY (concepto_id) REFERENCES Conceptos(ConceptoID)
        );
    """,
    'config_filtros_grupos': """
        CREATE TABLE config_filtros_grupos (
            id SERIAL PRIMARY KEY,
            grupo_id INTEGER NOT NULL,
            etiqueta VARCHAR(100) NOT NULL,
            activo_por_defecto BOOLEAN DEFAULT TRUE,
            
            CONSTRAINT fk_filtro_grupo FOREIGN KEY (grupo_id) REFERENCES Grupos(GrupoID),
            UNIQUE (grupo_id)
        );
    """,
    'tercero_descripciones': """
        CREATE TABLE tercero_descripciones (
            id SERIAL PRIMARY KEY,
            terceroid INT NOT NULL,
            descripcion TEXT,
            referencia TEXT,
            activa BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_tercero_master FOREIGN KEY (terceroid) REFERENCES Terceros(TerceroID)
        );
        
        -- Índice para búsqueda por descripción
        CREATE INDEX IF NOT EXISTS idx_tercero_descripciones_descripcion 
            ON tercero_descripciones(descripcion) 
            WHERE activa = TRUE;

        -- Índice para búsqueda por referencia
        CREATE INDEX IF NOT EXISTS idx_tercero_descripciones_referencia 
            ON tercero_descripciones(referencia) 
            WHERE referencia IS NOT NULL AND activa = TRUE;

        -- Índice para ordenamiento por tercero maestro
        CREATE INDEX IF NOT EXISTS idx_tercero_descripciones_terceroid 
            ON tercero_descripciones(terceroid);
    """
}


class ReiniciarTablasGUI:
    """Clase para la interfaz gráfica de reinicio de tablas."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Reiniciar Tablas - Base de Datos Mvtos")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Variables
        self.conn = None
        self.is_processing = False
        self.table_vars = {}
        self.table_info = {}  # Diccionario para almacenar info de tablas existentes
        
        self.setup_ui()
        self.cargar_info_tablas()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Reiniciar Tablas de Base de Datos", 
                                font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Frame de conexión
        conn_frame = ttk.LabelFrame(main_frame, text="Información de Conexión", padding="10")
        conn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(conn_frame, text=f"Base de datos: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}",
                  foreground="gray").grid(row=0, column=0, sticky=tk.W)
        
        # Frame de selección de tablas
        tables_frame = ttk.LabelFrame(main_frame, text="Seleccionar Tablas a Crear/Reiniciar", padding="10")
        tables_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        tables_frame.columnconfigure(0, weight=1)
        
        # Advertencia
        warning_frame = ttk.Frame(tables_frame)
        warning_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Label(warning_frame, text="ℹ️ Crea nuevas tablas o reinicia las existentes (elimina datos y recrea vacías)",
                  foreground="blue", font=("Arial", 9, "bold")).pack()
        
        # Botones de selección
        btn_frame = ttk.Frame(tables_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Button(btn_frame, text="Seleccionar Todas", 
                   command=self.select_all_tables).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Deseleccionar Todas", 
                   command=self.deselect_all_tables).pack(side=tk.LEFT, padx=5)
        self.refresh_button = ttk.Button(btn_frame, text="🔄 Actualizar", 
                                        command=self.cargar_info_tablas)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Checkboxes para cada tabla
        self.checkboxes_frame = ttk.Frame(tables_frame)
        self.checkboxes_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Se llenarán dinámicamente en cargar_info_tablas()
        
        # Frame de estadísticas
        stats_frame = ttk.LabelFrame(main_frame, text="Estadísticas de Tablas", padding="10")
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        stats_frame.columnconfigure(0, weight=1)
        
        self.stats_label = ttk.Label(stats_frame, text="Cargando información...", 
                                     font=("Courier", 9))
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # Área de log
        log_frame = ttk.LabelFrame(main_frame, text="Registro de Actividad", padding="5")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=90, 
                                                   wrap=tk.WORD, state='disabled',
                                                   font=("Courier", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar tags para colores
        self.log_text.tag_config('ERROR', foreground='red')
        self.log_text.tag_config('SUCCESS', foreground='green')
        self.log_text.tag_config('WARNING', foreground='orange')
        self.log_text.tag_config('INFO', foreground='blue')
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, pady=10)
        
        self.delete_button = ttk.Button(button_frame, text="🔄 Crear/Reiniciar Tablas Seleccionadas", 
                                       command=self.iniciar_reinicio, 
                                       style="Primary.TButton")
        self.delete_button.grid(row=0, column=0, padx=5)
        
        ttk.Button(button_frame, text="Limpiar Log", 
                   command=self.limpiar_log).grid(row=0, column=1, padx=5)
        
        # Estilo para botón
        style = ttk.Style()
        style.configure("Primary.TButton", foreground="blue")
        
        # Log inicial
        self.log("✓ Aplicación iniciada correctamente", 'SUCCESS')
        
    def log(self, mensaje, nivel='INFO'):
        """Agrega un mensaje al log con color según el nivel."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        
        # Determinar tag según nivel
        if 'Error' in mensaje or '✗' in mensaje or nivel == 'ERROR':
            tag = 'ERROR'
        elif '✓' in mensaje or 'exitosa' in mensaje.lower():
            tag = 'SUCCESS'
        elif '⚠️' in mensaje or nivel == 'WARNING':
            tag = 'WARNING'
        else:
            tag = 'INFO'
            
        self.log_text.insert(tk.END, f"[{timestamp}] {mensaje}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
        
    def limpiar_log(self):
        """Limpia el área de log."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
        
    def conectar(self):
        """Conecta a la base de datos."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            self.log(f"✗ Error al conectar: {e}", 'ERROR')
            return False
            
    def desconectar(self):
        """Cierra la conexión."""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    def cargar_info_tablas(self):
        """Carga información sobre las tablas existentes."""
        self.log("🔄 Actualizando información de tablas...", 'INFO')
        
        if not self.conectar():
            self.stats_label.config(text="Error: No se pudo conectar a la base de datos")
            return
            
        try:
            cursor = self.conn.cursor()
            self.table_info = {}
            total_registros = 0
            
            for tabla_info in TABLAS_INFO:
                tabla = tabla_info['name']
                try:
                    # Verificar si existe
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = %s
                        );
                    """, (tabla,))
                    
                    existe = cursor.fetchone()[0]
                    
                    if existe:
                        # Contar registros
                        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                        count = cursor.fetchone()[0]
                        self.table_info[tabla] = count
                        total_registros += count
                    else:
                        self.table_info[tabla] = None  # No existe
                        
                except Exception as e:
                    self.log(f"⚠️ Error al verificar tabla '{tabla}': {e}", 'WARNING')
                    self.table_info[tabla] = None
            
            cursor.close()
            
            # Actualizar estadísticas
            tablas_existentes = sum(1 for v in self.table_info.values() if v is not None)
            self.stats_label.config(
                text=f"Tablas encontradas: {tablas_existentes} de {len(TABLAS_INFO)} | "
                     f"Total de registros: {total_registros:,}"
            )
            
            # Recrear checkboxes con la información actualizada
            self.crear_checkboxes()
            
            self.log(f"✓ Información actualizada: {tablas_existentes} tabla(s) encontrada(s)", 'SUCCESS')
            
        except Exception as e:
            self.log(f"✗ Error al cargar información: {e}", 'ERROR')
        finally:
            self.desconectar()
            
    def crear_checkboxes(self):
        """Crea los checkboxes para cada tabla con su información."""
        # Limpiar checkboxes anteriores
        for widget in self.checkboxes_frame.winfo_children():
            widget.destroy()
        
        self.table_vars = {}
        
        row = 0
        for tabla_info in TABLAS_INFO:
            tabla = tabla_info['name']
            display = tabla_info['display']
            count = self.table_info.get(tabla)
            
            var = tk.BooleanVar(value=False)
            self.table_vars[tabla] = var
            
            # Estado de la tabla
            if count is None:
                estado = "(no existe - se creará)"
                estado_color = "orange"
            else:
                estado = f"({count:,} registros - se reiniciará)"
                estado_color = "blue"
            
            # Checkbox - SIEMPRE habilitado
            frame = ttk.Frame(self.checkboxes_frame)
            frame.grid(row=row, column=0, sticky=tk.W, pady=2)
            
            cb = ttk.Checkbutton(frame, text=f"{display}", variable=var,
                                state='normal')  # Siempre habilitado
            cb.pack(side=tk.LEFT)
            
            ttk.Label(frame, text=f" {estado}", 
                     foreground=estado_color, font=("Arial", 8)).pack(side=tk.LEFT)
            
            # Mostrar dependencias
            if tabla_info['depends_on']:
                dep_text = f"  → requiere: {', '.join(tabla_info['depends_on'])}"
                ttk.Label(self.checkboxes_frame, text=dep_text, 
                         foreground="gray", font=("Arial", 8)).grid(row=row, column=1, sticky=tk.W, padx=20)
            
            row += 1
            
    def select_all_tables(self):
        """Selecciona todas las tablas."""
        for var in self.table_vars.values():
            var.set(True)
                
    def deselect_all_tables(self):
        """Deselecciona todas las tablas."""
        for var in self.table_vars.values():
            var.set(False)
            
    def iniciar_reinicio(self):
        """Inicia el proceso de reinicio."""
        if self.is_processing:
            messagebox.showwarning("Advertencia", "Ya hay un proceso en ejecución.")
            return
            
        # Obtener tablas seleccionadas (todas las que estén marcadas)
        tablas_seleccionadas = [tabla for tabla, var in self.table_vars.items() if var.get()]
        
        if not tablas_seleccionadas:
            messagebox.showerror("Error", "No has seleccionado ninguna tabla.")
            return
            
        # Verificar dependencias
        for tabla in tablas_seleccionadas:
            tabla_info = next(t for t in TABLAS_INFO if t['name'] == tabla)
            for dep in tabla_info['depends_on']:
                if dep not in tablas_seleccionadas:
                    messagebox.showwarning(
                        "Advertencia de Dependencias",
                        f"La tabla '{tabla}' depende de '{dep}'.\n\n"
                        f"Se recomienda seleccionar también '{dep}'."
                    )
        
        # Separar tablas existentes y no existentes
        tablas_existentes = [t for t in tablas_seleccionadas if self.table_info.get(t) is not None]
        tablas_nuevas = [t for t in tablas_seleccionadas if self.table_info.get(t) is None]
        total_registros = sum(self.table_info.get(tabla, 0) for tabla in tablas_existentes)
        
        # Construir mensaje de confirmación
        mensaje = ""
        
        if tablas_nuevas:
            mensaje += f"✨ Se crearán {len(tablas_nuevas)} tabla(s) nueva(s):\n"
            for tabla in tablas_nuevas:
                mensaje += f"  • {tabla}\n"
            mensaje += "\n"
        
        if tablas_existentes:
            mensaje += f"⚠️ Se reiniciarán {len(tablas_existentes)} tabla(s) existente(s):\n"
            for tabla in tablas_existentes:
                count = self.table_info[tabla]
                mensaje += f"  • {tabla}: {count:,} registros serán eliminados\n"
            mensaje += f"\nTOTAL de registros a eliminar: {total_registros:,}\n\n"
        
        mensaje += "Todas las tablas quedarán vacías.\n\n¿Continuar?"
        
        respuesta = messagebox.askyesno("Confirmar Operación", mensaje, icon='question')
        
        if not respuesta:
            self.log("❌ Operación cancelada por el usuario", 'WARNING')
            return
            
        # Ejecutar en hilo separado
        self.is_processing = True
        self.delete_button.config(state='disabled')
        self.refresh_button.config(state='disabled')
        thread = threading.Thread(target=self.reiniciar_tablas, args=(tablas_seleccionadas,), daemon=True)
        thread.start()
    
    def crear_tabla(self, cursor, tabla):
        """Crea una tabla usando el SQL predefinido."""
        if tabla not in TABLE_CREATE_SQL:
            raise ValueError(f"No hay SQL de creación definido para la tabla '{tabla}'")
        
        cursor.execute(TABLE_CREATE_SQL[tabla])
        
    def reiniciar_tablas(self, tablas_seleccionadas):
        """Reinicia las tablas seleccionadas (DROP + CREATE)."""
        try:
            self.limpiar_log()
            self.log("="*70, 'INFO')
            self.log("INICIANDO CREACIÓN/REINICIO DE TABLAS", 'INFO')
            self.log("="*70, 'INFO')
            
            if not self.conectar():
                return
                
            cursor = self.conn.cursor()
            
            # Separar tablas existentes y nuevas
            tablas_existentes = [t for t in tablas_seleccionadas if self.table_info.get(t) is not None]
            tablas_nuevas = [t for t in tablas_seleccionadas if self.table_info.get(t) is None]
            
            # Configurar barra de progreso
            num_operaciones = len(tablas_existentes) + len(tablas_seleccionadas)  # DROP existentes + CREATE todas
            self.progress_bar['maximum'] = num_operaciones
            self.progress_bar['value'] = 0
            
            tablas_procesadas = []
            errores = []
            progreso = 0
            
            # Fase 1: Eliminar tablas existentes
            if tablas_existentes:
                self.log("\n📋 FASE 1: Eliminando tablas existentes...", 'INFO')
                for tabla in tablas_existentes:
                    try:
                        count = self.table_info[tabla]
                        self.log(f"🗑️ Eliminando tabla '{tabla}' ({count:,} registros)...", 'INFO')
                        
                        cursor.execute(f"DROP TABLE IF EXISTS {tabla} CASCADE")
                        self.conn.commit()
                        
                        self.log(f"✓ Tabla '{tabla}' eliminada", 'SUCCESS')
                        
                    except Exception as e:
                        self.log(f"✗ Error al eliminar tabla '{tabla}': {e}", 'ERROR')
                        errores.append((tabla, f"DROP: {str(e)}"))
                        self.conn.rollback()
                    
                    progreso += 1
                    self.progress_bar['value'] = progreso
            else:
                self.log("\nℹ️ No hay tablas existentes para eliminar", 'INFO')
            
            # Fase 2: Crear todas las tablas (en orden inverso para respetar dependencias)
            self.log("\n🔨 FASE 2: Creando tablas...", 'INFO')
            tablas_a_crear = list(reversed(tablas_seleccionadas))
            
            for tabla in tablas_a_crear:
                try:
                    accion = "Recreando" if tabla in tablas_existentes else "Creando"
                    self.log(f"🔨 {accion} tabla '{tabla}'...", 'INFO')
                    
                    self.crear_tabla(cursor, tabla)
                    self.conn.commit()
                    
                    self.log(f"✓ Tabla '{tabla}' {'recreada' if tabla in tablas_existentes else 'creada'} exitosamente", 'SUCCESS')
                    tablas_procesadas.append(tabla)
                    
                except Exception as e:
                    self.log(f"✗ Error al crear tabla '{tabla}': {e}", 'ERROR')
                    errores.append((tabla, f"CREATE: {str(e)}"))
                    self.conn.rollback()
                
                progreso += 1
                self.progress_bar['value'] = progreso
                
            cursor.close()
            
            # Resumen
            self.log("", 'INFO')
            self.log("="*70, 'INFO')
            self.log("RESUMEN DE LA OPERACIÓN", 'INFO')
            self.log("="*70, 'INFO')
            
            if tablas_procesadas:
                # Separar creadas vs recreadas
                tablas_creadas = [t for t in tablas_procesadas if t in tablas_nuevas]
                tablas_recreadas = [t for t in tablas_procesadas if t in tablas_existentes]
                
                if tablas_creadas:
                    self.log(f"✓ Tablas creadas: {len(tablas_creadas)}", 'SUCCESS')
                    for tabla in tablas_creadas:
                        self.log(f"  ✓ {tabla} (nueva)", 'SUCCESS')
                
                if tablas_recreadas:
                    self.log(f"✓ Tablas recreadas: {len(tablas_recreadas)}", 'SUCCESS')
                    for tabla in tablas_recreadas:
                        self.log(f"  ✓ {tabla} (reiniciada)", 'SUCCESS')
                    
            if errores:
                self.log(f"✗ Errores encontrados: {len(errores)}", 'ERROR')
                for tabla, error in errores:
                    self.log(f"  ✗ {tabla}: {error}", 'ERROR')
                    
            self.log("="*70, 'INFO')
            
            if not errores and tablas_procesadas:
                self.log("✓✓✓ PROCESO COMPLETADO EXITOSAMENTE ✓✓✓", 'SUCCESS')
                messagebox.showinfo("Éxito", 
                                   f"Se procesaron {len(tablas_procesadas)} tabla(s) exitosamente.\n"
                                   f"Las tablas están vacías y listas para cargar datos.")
            elif errores:
                messagebox.showwarning("Completado con Errores",
                                      f"Se procesaron {len(tablas_procesadas)} tabla(s).\n"
                                      f"Se encontraron {len(errores)} error(es).")
                                      
            # Actualizar información de tablas
            self.cargar_info_tablas()
            
        except Exception as e:
            self.log(f"✗ Error crítico: {e}", 'ERROR')
            messagebox.showerror("Error Crítico", f"Error:\n{e}")
        finally:
            self.desconectar()
            self.is_processing = False
            self.delete_button.config(state='normal')
            self.refresh_button.config(state='normal')
            self.progress_bar['value'] = 0


def main():
    """Función principal."""
    root = tk.Tk()
    app = ReiniciarTablasGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
