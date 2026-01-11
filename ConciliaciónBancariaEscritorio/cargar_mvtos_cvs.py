
import psycopg2
from psycopg2 import sql
import csv
from datetime import datetime
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import os

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

class CargadorMvtosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cargador de Movimientos")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Variables
        self.running = False
        self.archivo_csv = None
        self.reiniciar_tabla = tk.BooleanVar(value=False)
        self.datos_para_cargar = []  # Lista para almacenar datos analizados
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Carga de Datos - Mvtos", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Frame de información de BD
        db_frame = ttk.LabelFrame(main_frame, text="Base de Datos", padding="10")
        db_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(db_frame, text=f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(db_frame, text=f"Database: {DB_CONFIG['database']}").grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        ttk.Label(db_frame, text="Tabla: movimientos").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        
        # Frame de selección de archivo
        file_frame = ttk.LabelFrame(main_frame, text="Archivo CSV", padding="10")
        file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Archivo:").grid(row=0, column=0, sticky=tk.W)
        self.file_label = ttk.Label(file_frame, text="Ningún archivo seleccionado", 
                                    foreground='gray', font=('Arial', 9))
        self.file_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 10))
        
        self.browse_button = ttk.Button(file_frame, text="Seleccionar Archivo...", 
                                       command=self.seleccionar_archivo)
        self.browse_button.grid(row=0, column=2, sticky=tk.E)
        
        # Checkbox para reiniciar tabla
        self.reiniciar_check = ttk.Checkbutton(file_frame, 
                                               text="Reiniciar tabla antes de cargar (eliminar datos existentes)",
                                               variable=self.reiniciar_tabla)
        self.reiniciar_check.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        # Frame de progreso
        progress_frame = ttk.LabelFrame(main_frame, text="Progreso", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(1, weight=1)
        
        # Etiqueta de estado
        ttk.Label(progress_frame, text="Estado:").grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(progress_frame, text="Listo para comenzar", 
                                      font=('Arial', 9, 'bold'))
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Barra de progreso
        ttk.Label(progress_frame, text="Progreso:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(10, 0))
        
        # Frame de contador
        self.counter_label = ttk.Label(progress_frame, text="Registros: 0 / 0", font=('Arial', 9))
        self.counter_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))

        # Frame de Vista Previa (Nuevo)
        preview_frame = ttk.LabelFrame(main_frame, text="Vista Previa de Datos", padding="10")
        preview_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)

        # Treeview
        # Treeview
        columns = ('fecha', 'cuenta', 'valor', 'usd', 'trm', 'moneda', 'tercero', 'grupo', 'concepto', 'detalle', 'descripcion', 'referencia')
        self.tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=8)
        
        # Encabezados
        self.tree.heading('fecha', text='Fecha')
        self.tree.heading('cuenta', text='Cuenta ID')
        self.tree.heading('valor', text='Valor')
        self.tree.heading('usd', text='USD')
        self.tree.heading('trm', text='TRM')
        self.tree.heading('moneda', text='Moneda ID')
        self.tree.heading('tercero', text='Tercero ID')
        self.tree.heading('grupo', text='Grupo ID')
        self.tree.heading('concepto', text='Concepto ID')
        self.tree.heading('detalle', text='Detalle')
        self.tree.heading('descripcion', text='Descripción')
        self.tree.heading('referencia', text='Referencia')
        
        # Acceso directo para configuración de columnas
        self.tree.column('fecha', width=80)
        self.tree.column('cuenta', width=60)
        self.tree.column('valor', width=90)
        self.tree.column('usd', width=70)
        self.tree.column('trm', width=60)
        self.tree.column('moneda', width=60)
        self.tree.column('tercero', width=60)
        self.tree.column('grupo', width=60)
        self.tree.column('concepto', width=60)
        self.tree.column('detalle', width=150)
        self.tree.column('descripcion', width=150)
        self.tree.column('referencia', width=100)
        
        # Scrollbar para treeview
        tree_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # Scrollbar horizontal
        tree_scroll_h = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=tree_scroll_h.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Frame de estadísticas
        stats_frame = ttk.LabelFrame(main_frame, text="Estadísticas de Vista Previa", padding="10")
        stats_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=4, width=80, font=('Courier', 9))
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        stats_frame.columnconfigure(0, weight=1)
        
        # Frame de log
        log_frame = ttk.LabelFrame(main_frame, text="Log de Eventos", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Área de texto con scroll para el log
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=80, 
                                                   font=('Courier', 9), state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar colores para el log
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('info', foreground='blue')
        
        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))
        
        self.analyze_button = ttk.Button(button_frame, text="Analizar CSV (Vista Previa)", 
                                       command=self.iniciar_analisis, width=25)
        self.analyze_button.grid(row=0, column=0, padx=5)

        self.save_button = ttk.Button(button_frame, text="Autorizar Carga a BD", 
                                       command=self.iniciar_guardado, width=25, state='disabled')
        self.save_button.grid(row=0, column=1, padx=5)
        
        self.clear_button = ttk.Button(button_frame, text="Limpiar Log", 
                                       command=self.limpiar_log, width=20)
        self.clear_button.grid(row=0, column=2, padx=5)
        
        # Log inicial
        self.agregar_log("✓ Aplicación iniciada correctamente", 'success')
        self.agregar_log("📁 Selecciona un archivo CSV y haz clic en 'Analizar CSV'", 'info')
    
    def seleccionar_archivo(self):
        """Abre un diálogo para seleccionar el archivo CSV."""
        initial_dir = r"F:\1. Cloud\4. AI\1. Antigravity\Conciliación Bancaria"
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        archivo = filedialog.askopenfilename(
            title="Seleccionar Archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            initialdir=initial_dir
        )
        
        if archivo:
            self.archivo_csv = archivo
            nombre_archivo = os.path.basename(archivo)
            self.file_label.config(text=nombre_archivo, foreground='black', font=('Arial', 9, 'bold'))
            self.agregar_log(f"✓ Archivo seleccionado: {nombre_archivo}", 'success')
            self.datos_para_cargar = []
            self.save_button.config(state='disabled')
            self.tree.delete(*self.tree.get_children())
    
    def agregar_log(self, mensaje, tipo='info'):
        """Agrega un mensaje al log con timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {mensaje}\n", tipo)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
    
    def actualizar_status(self, mensaje):
        """Actualiza la etiqueta de estado."""
        self.status_label.config(text=mensaje)
        self.root.update_idletasks()
    
    def actualizar_progreso(self, actual, total):
        """Actualiza la barra de progreso y el contador."""
        if total > 0:
            porcentaje = (actual / total) * 100
            self.progress_bar['value'] = porcentaje
            self.counter_label.config(text=f"Registros: {actual} / {total}")
        self.root.update_idletasks()
    
    def actualizar_estadisticas(self, stats):
        """Actualiza el área de estadísticas."""
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', stats)
        self.root.update_idletasks()
    
    def limpiar_log(self):
        """Limpia el área de log y la vista previa."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
        
        # Limpiar treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.datos_para_cargar = []
        self.save_button.config(state='disabled')
        self.agregar_log("Log y datos limpiados", 'info')
    
    def iniciar_analisis(self):
        """Inicia el análisis del CSV en un thread separado."""
        if not self.archivo_csv:
            messagebox.showwarning("Advertencia", "Por favor selecciona un archivo CSV primero.")
            return
        
        if not os.path.exists(self.archivo_csv):
            messagebox.showerror("Error", "El archivo seleccionado no existe.")
            return
            
        if not self.running:
            self.running = True
            self.analyze_button.config(state='disabled')
            self.save_button.config(state='disabled')
            self.browse_button.config(state='disabled')
            self.limpiar_log()
            thread = threading.Thread(target=self.ejecutar_analisis)
            thread.daemon = True
            thread.start()

    def ejecutar_analisis(self):
        """Lee el CSV y muestra la vista previa."""
        try:
            self.actualizar_status("Analizando CSV...")
            self.agregar_log(f"📂 Iniciando análisis de '{os.path.basename(self.archivo_csv)}'...", 'info')
            
            self.datos_para_cargar = []
            registros_validos = 0
            registros_erroneos = 0
            total_valor = 0
            
            # Limpiar treeview existente
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Contar lineas
            with open(self.archivo_csv, 'r', encoding='utf-8-sig') as f:
                total_registros = sum(1 for line in f) - 1
            
            self.agregar_log(f"📊 Registros detectados: {total_registros}", 'info')
            self.actualizar_progreso(0, total_registros)

            with open(self.archivo_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Normalizar fieldnames a minúsculas y sin espacios para comparación interna si es necesario, 
                # pero csv.DictReader usa los headers tal cual.
                # Vamos a manejar el acceso de forma flexible.
                
                for num_linea, row in enumerate(reader, start=2):
                    try:
                        # Helper para buscar keys insensitivamente
                        def get_val(keys):
                            if isinstance(keys, str): keys = [keys]
                            for k in keys:
                                # Busqueda exacta
                                if k in row and row[k]: return row[k]
                                # Busqueda insensible a mayusculas en las keys del row
                                for row_k in row.keys():
                                    if row_k and row_k.strip().lower() == k.lower() and row[row_k]:
                                        return row[row_k]
                            return None

                        # Parsear datos
                        fecha = self.parsear_fecha(get_val(['Fecha', 'Date']))
                        descripcion = (get_val(['Descripción', 'Descripcion', 'Description']) or '').strip()
                        referencia = (get_val(['Referencia', 'Reference']) or '').strip()
                        valor = self.parsear_valor(get_val(['Valor', 'Value', 'Amount']))
                        
                        usd = self.parsear_valor(get_val(['Valor USD', 'USD']))
                        trm = self.parsear_valor(get_val(['TRM', 'Exchange Rate']))
                        
                        moneda_id = self.parsear_entero(get_val(['Moneda ID', 'MonedaID', 'CurrencyID', 'monedaid']))
                        cuenta_id = self.parsear_entero(get_val(['Cuenta ID', 'CuentaID', 'AccountID', 'cuentaid']))
                        tercero_id = self.parsear_entero(get_val(['Tercero ID', 'TerceroID', 'ContactID', 'terceroid']))
                        grupo_id = self.parsear_entero(get_val(['Grupo ID', 'GrupoID', 'GroupID', 'grupoid']))
                        concepto_id = self.parsear_entero(get_val(['Concepto ID', 'ConceptoID', 'ConceptID', 'conceptoid']))
                        detalle = (get_val(['Detalle', 'Detail']) or '').strip()

                        data_row = {
                            'fecha': fecha, 'descripcion': descripcion, 'referencia': referencia,
                            'valor': valor, 'usd': usd, 'trm': trm, 'moneda_id': moneda_id,
                            'cuenta_id': cuenta_id, 'tercero_id': tercero_id, 'grupo_id': grupo_id,
                            'concepto_id': concepto_id, 'detalle': detalle
                        }
                        
                        self.datos_para_cargar.append(data_row)
                        
                        if valor: total_valor += valor
                        registros_validos += 1

                        # Insertar en treeview (solo mostrar primeros 1000 para rendimiento si es muy grande, o todos si es manejable)
                        # El usuario pidió ver los registros, mostraremos todos pero con cuidado. 
                        # Treeview aguanta unos miles. Si son muchos, limitamos.
                        self.tree.insert('', 'end', values=(
                            fecha, 
                            cuenta_id if cuenta_id else '', 
                            valor, 
                            usd if usd else '',
                            trm if trm else '',
                            moneda_id if moneda_id else '',
                            tercero_id if tercero_id else '', 
                            grupo_id if grupo_id else '', 
                            concepto_id if concepto_id else '',
                            detalle,
                            descripcion,
                            referencia
                        ))

                        if registros_validos % 10 == 0:
                            self.actualizar_progreso(registros_validos, total_registros)

                    except Exception as e:
                        registros_erroneos += 1
                        self.agregar_log(f"⚠ Error leyendo línea {num_linea}: {e}", 'warning')

            self.actualizar_progreso(total_registros, total_registros)
            
            # Estadísticas previas
            stats = f"Registros leídos: {registros_validos}\n"
            stats += f"Registros con error: {registros_erroneos}\n"
            stats += f"Suma Valor: ${total_valor:,.2f}"
            self.actualizar_estadisticas(stats)

            if registros_validos > 0:
                self.save_button.config(state='normal')
                self.agregar_log(f"✓ Análisis completado. {registros_validos} registros listos para cargar.", 'success')
                self.actualizar_status("Esperando autorización...")
            else:
                self.agregar_log("✗ No se encontraron registros válidos para cargar.", 'error')
                self.actualizar_status("Error en análisis")

        except Exception as e:
            self.agregar_log(f"✗ Error crítico analizando CSV: {e}", 'error')
            self.actualizar_status("Error crítico")
        
        finally:
            self.running = False
            self.analyze_button.config(state='normal')
            self.browse_button.config(state='normal')

    def iniciar_guardado(self):
        """Inicia el guardado en BD."""
        if not self.datos_para_cargar:
            return

        if self.reiniciar_tabla.get():
            respuesta = messagebox.askyesno(
                "Confirmar Reinicio",
                "¿Estás seguro de eliminar TODOS los datos existentes en la tabla antes de cargar?\nEsta acción no se puede deshacer.",
                icon='warning'
            )
            if not respuesta: return

        if not self.running:
            self.running = True
            self.analyze_button.config(state='disabled')
            self.save_button.config(state='disabled')
            self.browse_button.config(state='disabled')
            self.reiniciar_check.config(state='disabled')
            
            thread = threading.Thread(target=self.ejecutar_guardado)
            thread.daemon = True
            thread.start()

    def ejecutar_guardado(self):
        """Ejecuta la inserción en BD."""
        conn = None
        try:
            self.actualizar_status("Conectando a BD...")
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            if not self.crear_tabla(cursor):
                return
            
            # Reiniciar si aplica
            if self.reiniciar_tabla.get():
                self.actualizar_status("Limpiando tabla...")
                cursor.execute("TRUNCATE TABLE movimientos RESTART IDENTITY CASCADE")
                conn.commit()
                self.agregar_log("🗑️ Tabla reiniciada.", 'warning')

            self.actualizar_status(f"Cargando {len(self.datos_para_cargar)} registros...")
            self.agregar_log("🚀 Iniciando inserción en base de datos...", 'info')

            sql_insert = """
            INSERT INTO movimientos 
            (Fecha, Descripcion, Referencia, Valor, USD, TRM, 
             MonedaID, CuentaID, TerceroID, GrupoID, ConceptoID, Detalle)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            insertados = 0
            total = len(self.datos_para_cargar)
            
            for i, row in enumerate(self.datos_para_cargar):
                cursor.execute(sql_insert, (
                    row['fecha'], row['descripcion'], row['referencia'], row['valor'],
                    row['usd'], row['trm'], row['moneda_id'], row['cuenta_id'],
                    row['tercero_id'], row['grupo_id'], row['concepto_id'], row['detalle']
                ))
                insertados += 1
                if insertados % 50 == 0:
                    conn.commit()
                    self.actualizar_progreso(insertados, total)
            
            conn.commit()
            self.actualizar_progreso(total, total)
            
            self.agregar_log(f"✓ Carga finalizada exitosamente. {insertados} registros insertados.", 'success')
            self.actualizar_status("Carga completa")
            
            # Verificación final
            self.verificar_datos(cursor)
            
            # Limpiar datos pendientes para evitar doble carga accidental
            self.datos_para_cargar = []
            
        except Exception as e:
            if conn: conn.rollback()
            self.agregar_log(f"✗ Error guardando en BD: {e}", 'error')
            self.actualizar_status("Error en guardado")
        
        finally:
            if conn: conn.close()
            self.running = False
            self.analyze_button.config(state='normal')
            self.browse_button.config(state='normal')
            self.reiniciar_check.config(state='normal')
            # Dejar el botón de guardar deshabilitado hasta nuevo análisis
            self.save_button.config(state='disabled')
    
    def crear_tabla(self, cursor):
        """Crea la tabla Mvtos si no existe."""
        sql_crear_tabla = """
        CREATE TABLE IF NOT EXISTS movimientos (
            Id SERIAL PRIMARY KEY,
            Fecha DATE NOT NULL,
            Descripcion VARCHAR(500),
            Referencia VARCHAR(100),
            Valor DECIMAL(15, 2),
            USD DECIMAL(15, 2),
            TRM DECIMAL(10, 4),
            MonedaID INTEGER,
            CuentaID INTEGER,
            TerceroID INTEGER,
            GrupoID INTEGER,
            ConceptoID INTEGER,
            Detalle VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT fk_moneda FOREIGN KEY (MonedaID) REFERENCES Monedas(MonedaID),
            CONSTRAINT fk_cuenta FOREIGN KEY (CuentaID) REFERENCES Cuentas(CuentaID),
            CONSTRAINT fk_tercero FOREIGN KEY (TerceroID) REFERENCES Terceros(TerceroID),
            CONSTRAINT fk_grupo FOREIGN KEY (GrupoID) REFERENCES Grupos(GrupoID),
            CONSTRAINT fk_concepto FOREIGN KEY (ConceptoID) REFERENCES Conceptos(ConceptoID)
        );
        """
        
        try:
            cursor.execute(sql_crear_tabla)
            return True
        except Exception as e:
            self.agregar_log(f"✗ Error al crear la tabla: {e}", 'error')
            self.actualizar_status("Error al crear tabla")
            return False
    
    def parsear_fecha(self, fecha_str):
        """Convierte una fecha en formato DD/MMM/YYYY o YYYY-MM-DD a objeto datetime."""
        if not fecha_str or str(fecha_str).strip() == '':
            return None
        
        fecha_str = str(fecha_str).strip()
        
        # Intentar formato YYYY-MM-DD primero (formato ISO estándar)
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            pass  # Si falla, intentar el siguiente formato
        
        try:
            # Diccionarios de meses (Inglés y Español)
            meses = {
                # Inglés
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                # Español
                'ene': 1, 'abr': 4, 'ago': 8, 'dic': 12
            }
            # Completar mapeo español si faltan o si se solapan con inglés
            meses_es = {
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
            }
            meses.update(meses_es)
            
            partes = fecha_str.split('/')
            if len(partes) != 3:
                # Intentar con guiones
                partes = fecha_str.split('-')
                if len(partes) != 3:
                    raise ValueError("Formato de fecha no reconocido")
            
            # Limpiar espacios y normalizar mes
            p1 = partes[0].strip()
            p2 = partes[1].strip().lower()
            p3 = partes[2].strip()
            
            # Detectar formato YYYY/MMM/DD vs DD/MMM/YYYY
            if p1.isdigit() and int(p1) > 31:
                # Formato YYYY/MMM/DD
                año = int(p1)
                mes = meses.get(p2)
                dia = int(p3)
            else:
                # Formato DD/MMM/YYYY
                dia = int(p1)
                mes = meses.get(p2)
                año = int(p3)
                
            if mes is None:
                # Intentar si el mes es numérico
                if p2.isdigit():
                    mes = int(p2)
                else:
                    raise ValueError(f"Mes desconocido: {p2}")
            
            return datetime(año, mes, dia).date()
        except Exception as e:
            self.agregar_log(f"⚠ Error al parsear fecha '{fecha_str}': {e}", 'warning')
            return None
    
    def parsear_valor(self, valor_str):
        """Convierte un valor en formato de texto a decimal."""
        if not valor_str or str(valor_str).strip() == '':
            return None
        
        try:
            valor = str(valor_str).strip()
            es_negativo = False
            
            if valor.startswith('(') and valor.endswith(')'):
                es_negativo = True
                valor = valor[1:-1]
            
            valor = valor.replace(',', '')
            resultado = float(valor)
            
            if es_negativo:
                resultado = -resultado
            
            return resultado
        except Exception as e:
            self.agregar_log(f"⚠ Error al parsear valor '{valor_str}': {e}", 'warning')
            return None
    
    def parsear_entero(self, valor_str):
        """Convierte un valor de texto a entero."""
        if not valor_str or str(valor_str).strip() == '':
            return None
        try:
            return int(str(valor_str).strip())
        except:
            return None

    def verificar_datos(self, cursor):
        """Ejecuta consultas de verificación para validar la carga de datos."""
        try:
            stats = ""
            
            # Total de registros
            cursor.execute("SELECT COUNT(*) FROM movimientos")
            total = cursor.fetchone()[0]
            stats += f"Total de registros: {total}\n"
            
            # Rango de fechas
            cursor.execute("SELECT MIN(Fecha), MAX(Fecha) FROM movimientos")
            fechas = cursor.fetchone()
            stats += f"Período: {fechas[0]} a {fechas[1]}\n"
            
            # Suma total
            cursor.execute("SELECT SUM(Valor) FROM movimientos")
            suma_total = cursor.fetchone()[0]
            if suma_total:
                stats += f"Suma total: ${suma_total:,.2f}\n"
            else:
                stats += f"Suma total: $0.00\n"
            
            # Foreign keys
            cursor.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE MonedaID IS NOT NULL) as moneda,
                    COUNT(*) FILTER (WHERE CuentaID IS NOT NULL) as cuenta,
                    COUNT(*) FILTER (WHERE TerceroID IS NOT NULL) as tercero,
                    COUNT(*) FILTER (WHERE GrupoID IS NOT NULL) as grupo,
                    COUNT(*) FILTER (WHERE ConceptoID IS NOT NULL) as concepto
                FROM movimientos
            """)
            fks = cursor.fetchone()
            stats += f"FKs: Moneda={fks[0]}, Cuenta={fks[1]}, Tercero={fks[2]}, Grupo={fks[3]}, Concepto={fks[4]}"
            
            self.actualizar_estadisticas(stats)
            self.agregar_log("✓ Verificación de datos completada", 'success')
            
        except Exception as e:
            self.agregar_log(f"✗ Error en verificación: {e}", 'error')

def main():
    """Función principal."""
    root = tk.Tk()
    app = CargadorMvtosGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
