#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cargador de Movimientos Bancarios - Interfaz Gráfica
Permite cargar movimientos bancarios desde archivos PDF, validando duplicados
contra la base de datos PostgreSQL.

Autor: Antigravity
Fecha: 2025-12-28
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import psycopg2
from psycopg2 import sql
from datetime import datetime
from decimal import Decimal
import threading
import os
import sys

# Importar extractores - agregar directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from extractores.bancolombia_extractor import (
    extraer_movimientos_bancolombia,
    obtener_estadisticas
)
from extractores.fondorenta_extractor import extraer_movimientos_fondorenta
from extractores.creditcard_extractor import extraer_movimientos_credito

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

# Funciones auxiliares para detección de patrones
def detectar_cuota_manejo(descripcion):
    """
    Detecta si una descripción corresponde a cuota de manejo.
    Retorna True si coincide con los patrones.
    """
    if not descripcion:
        return False
    
    desc_lower = descripcion.lower()
    patrones = [
        'cuota' in desc_lower and 'manejo' in desc_lower,
        'manejo' in desc_lower and 'tarjeta' in desc_lower,
        'dev' in desc_lower and 'cuota' in desc_lower and 'manejo' in desc_lower
    ]
    
    return any(patrones)


def obtener_contactid_bancolombia(cursor):
    """
    Obtiene el TerceroID del contacto 'Bancolombia' con referencia 'Cuota de Manejo'.
    Retorna el TerceroID o None si no existe.
    """
    try:
        cursor.execute("""
            SELECT terceroid 
            FROM terceros 
            WHERE tercero = 'Bancolombia' 
              AND referencia = 'Cuota de Manejo'
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception:
        return None


# Configuración de cuentas
CUENTAS_CONFIG = {
    'Ahorros': {
        'account_id': 2,
        'extractor': extraer_movimientos_bancolombia,
        'file_filter': [("PDF Files", "*.pdf"), ("All Files", "*.*")]
    },
    'Fondorenta': {
        'account_id': 3,
        'extractor': extraer_movimientos_fondorenta,
        'file_filter': [("PDF Files", "*.pdf"), ("All Files", "*.*")]
    },
    'Mc Pesos': {
        'account_id': 4,
        'extractor': extraer_movimientos_credito,
        'file_filter': [("PDF Files", "*.pdf"), ("All Files", "*.*")]
    },
    'Mc Dolaras': {
        'account_id': 5,
        'extractor': extraer_movimientos_credito,
        'file_filter': [("PDF Files", "*.pdf"), ("All Files", "*.*")]
    },
    'Tarjeta Crédito (Smart)': {
        'account_id': 4, # Default a Pesos, pero cambiará dinámicamente
        'extractor': extraer_movimientos_credito,
        'file_filter': [("PDF Files", "*.pdf"), ("All Files", "*.*")]
    },
    'Protección': {
        'account_id': 7,
        'extractor': None,  # TODO: implementar
        'file_filter': [("All Files", "*.*")]
    }
}


class CargadorMovimientosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cargador de Movimientos Bancarios")
        self.root.geometry("1100x800")
        self.root.resizable(True, True)
        
        # Variables
        self.cuenta_seleccionada = tk.StringVar(value="Ahorros")
        self.archivo_pdf = None
        self.movimientos_extraidos = []
        self.movimientos_nuevos = []
        self.movimientos_duplicados = []
        self.running = False
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
        # Log inicial
        self.agregar_log("✓ Aplicación iniciada correctamente", 'success')
        self.agregar_log("📁 Selecciona una cuenta y un archivo PDF para comenzar", 'info')
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)  # Preview
        main_frame.rowconfigure(6, weight=1)  # Log
        
        # Título
        title_label = ttk.Label(main_frame, text="Cargador de Movimientos Bancarios", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # === SECCIÓN 1: Selección de Cuenta y Archivo ===
        selection_frame = ttk.LabelFrame(main_frame, text="1. Selección de Cuenta y Archivo", padding="10")
        selection_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        selection_frame.columnconfigure(1, weight=1)
        
        # Selector de cuenta
        ttk.Label(selection_frame, text="Cuenta:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        cuenta_combo = ttk.Combobox(selection_frame, textvariable=self.cuenta_seleccionada,
                                    values=list(CUENTAS_CONFIG.keys()), state='readonly', width=30)
        cuenta_combo.grid(row=0, column=1, sticky=tk.W)
        
        # Selector de archivo
        ttk.Label(selection_frame, text="Archivo:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.file_label = ttk.Label(selection_frame, text="Ningún archivo seleccionado", 
                                    foreground='gray', font=('Arial', 9))
        self.file_label.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        self.browse_button = ttk.Button(selection_frame, text="Seleccionar Archivo...", 
                                       command=self.seleccionar_archivo)
        self.browse_button.grid(row=1, column=2, sticky=tk.E, padx=(10, 0), pady=(10, 0))
        
        # === SECCIÓN 2: Estadísticas ===
        stats_frame = ttk.LabelFrame(main_frame, text="2. Estadísticas de Validación", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Container para las tres cajas de estadísticas
        stats_container = ttk.Frame(stats_frame)
        stats_container.grid(row=0, column=0, pady=5)
        
        # Caja 1: Registros Leídos
        box1 = ttk.Frame(stats_container, relief='solid', borderwidth=2)
        box1.grid(row=0, column=0, padx=10)
        ttk.Label(box1, text="📊 Registros Leídos", font=('Arial', 9, 'bold')).pack(pady=(5, 0))
        self.stats_leidos = ttk.Label(box1, text="0", font=('Arial', 20, 'bold'), foreground='blue')
        self.stats_leidos.pack(pady=(0, 5), padx=20)
        
        # Caja 2: Duplicados
        box2 = ttk.Frame(stats_container, relief='solid', borderwidth=2)
        box2.grid(row=0, column=1, padx=10)
        ttk.Label(box2, text="⚠ Duplicados", font=('Arial', 9, 'bold')).pack(pady=(5, 0))
        self.stats_duplicados = ttk.Label(box2, text="0", font=('Arial', 20, 'bold'), foreground='orange')
        self.stats_duplicados.pack(pady=(0, 5), padx=20)
        
        # Caja 3: A Cargar
        box3 = ttk.Frame(stats_container, relief='solid', borderwidth=2)
        box3.grid(row=0, column=2, padx=10)
        ttk.Label(box3, text="✓ A Cargar", font=('Arial', 9, 'bold')).pack(pady=(5, 0))
        self.stats_a_cargar = ttk.Label(box3, text="0", font=('Arial', 20, 'bold'), foreground='green')
        self.stats_a_cargar.pack(pady=(0, 5), padx=20)
        
        # === SECCIÓN 3: Preview de Datos ===
        preview_frame = ttk.LabelFrame(main_frame, text="3. Preview de Todos los Datos Extraídos", padding="10")
        preview_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # TreeView para mostrar movimientos
        columns = ('fecha', 'descripcion', 'referencia', 'valor')
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=8)
        
        self.preview_tree.heading('fecha', text='Fecha')
        self.preview_tree.heading('descripcion', text='Descripción')
        self.preview_tree.heading('referencia', text='Referencia')
        self.preview_tree.heading('valor', text='Valor')
        
        self.preview_tree.column('fecha', width=100)
        self.preview_tree.column('descripcion', width=500)
        self.preview_tree.column('referencia', width=150)
        self.preview_tree.column('valor', width=120, anchor='e')
        
        # Scrollbars
        vsb = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        hsb = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.preview_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # === SECCIÓN 4: Validación ===
        validation_frame = ttk.LabelFrame(main_frame, text="4. Validación de Duplicados", padding="10")
        validation_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        validation_frame.columnconfigure(0, weight=1)
        
        self.validation_text = tk.Text(validation_frame, height=10, width=80, font=('Courier', 9))
        self.validation_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # === SECCIÓN 5: Progreso y Acciones ===
        action_frame = ttk.LabelFrame(main_frame, text="5. Acciones", padding="10")
        action_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        action_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(action_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botones de acción
        button_container = ttk.Frame(action_frame)
        button_container.grid(row=1, column=0)
        
        self.load_button = ttk.Button(button_container, text="✓ Cargar Registros Nuevos", 
                                     command=self.cargar_registros, state='disabled', width=25)
        self.load_button.grid(row=0, column=0, padx=5)
        
        self.clear_button = ttk.Button(button_container, text="🗑️ Limpiar", 
                                      command=self.limpiar_todo, width=20)
        self.clear_button.grid(row=0, column=1, padx=5)
        
        # === SECCIÓN 6: Log de Eventos ===
        log_frame = ttk.LabelFrame(main_frame, text="Log de Eventos", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Área de texto con scroll para el log
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80, 
                                                   font=('Courier', 9), state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar colores para el log
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('info', foreground='blue')
    


    def _centrar_caja_dialogo(self, ventana, ancho_min=350, alto_min=180):
        """Centra una ventana emergente (Toplevel) sobre la ventana principal."""
        self.root.update_idletasks()
        ventana.update_idletasks()
        
        w = ventana.winfo_reqwidth()
        h = ventana.winfo_reqheight()
        
        # Asegurar un tamaño mínimo y razonable
        w = max(w, ancho_min)
        h = max(h, alto_min)
        
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        
        x = root_x + (root_w - w) // 2
        y = root_y + (root_h - h) // 2
        
        ventana.geometry(f"{w}x{h}+{x}+{y}")

    def mostrar_mensaje_custom(self, title, message, type='info'):
        """Muestra un mensaje modal centrado."""
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.transient(self.root)
        dlg.grab_set()
        
        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono (simulado con texto/color)
        colors = {'info': '#0055aa', 'warning': '#ffaa00', 'error': '#cc0000', 'success': '#008800'}
        icon_char = {'info': 'ℹ', 'warning': '⚠', 'error': '✗', 'success': '✓'}
        
        fg_color = colors.get(type, 'black')
        char = icon_char.get(type, 'ℹ')
        
        ttk.Label(frame, text=char, font=('Arial', 24), foreground=fg_color).pack(pady=(0, 10))
        ttk.Label(frame, text=message, wraplength=380, justify=tk.CENTER, font=('Arial', 10)).pack(pady=(0, 20))
        
        ttk.Button(frame, text="Aceptar", command=dlg.destroy).pack()
        
        self._centrar_caja_dialogo(dlg)
        self.root.wait_window(dlg)

    def preguntar_si_no_custom(self, title, message):
        """Muestra pregunta Sí/No centrada. Retorna True/False."""
        result = {'value': False}
        
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.transient(self.root)
        dlg.grab_set()
        
        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="?", font=('Arial', 24), foreground='#0055aa').pack(pady=(0, 10))
        ttk.Label(frame, text=message, wraplength=380, justify=tk.CENTER, font=('Arial', 10)).pack(pady=(0, 20))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        
        def yes():
            result['value'] = True
            dlg.destroy()
            
        def no():
            result['value'] = False
            dlg.destroy()
            
        ttk.Button(btn_frame, text="Sí", command=yes, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="No", command=no, width=10).pack(side=tk.LEFT, padx=10)
        
        self._centrar_caja_dialogo(dlg)
        self.root.wait_window(dlg)
        
        return result['value']


    def mostrar_dialogo_seleccion(self, movimientos):
        """
        Muestra un diálogo para seleccionar qué movimientos cargar.
        Retorna la lista de movimientos seleccionados o None si se cancela.
        """
        dlg = tk.Toplevel(self.root)
        dlg.title("Selección de Movimientos")
        dlg.geometry("900x600")
        dlg.transient(self.root)
        dlg.grab_set()
        
        # Header
        header = ttk.Frame(dlg, padding=10)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Seleccione los movimientos a cargar:", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # Main area with scrollbar
        main_frame = ttk.Frame(dlg, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Ensure width matches canvas
        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)

        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Headers del listado
        h_frame = ttk.Frame(scrollable_frame)
        h_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(h_frame, text="Sel", width=5, font=('Arial', 9, 'bold')).grid(row=0, column=0)
        ttk.Label(h_frame, text="Fecha", width=12, font=('Arial', 9, 'bold')).grid(row=0, column=1)
        ttk.Label(h_frame, text="Moneda", width=8, font=('Arial', 9, 'bold')).grid(row=0, column=2)
        ttk.Label(h_frame, text="Importe Original", width=15, font=('Arial', 9, 'bold')).grid(row=0, column=3)
        ttk.Label(h_frame, text="Descripción", width=50, font=('Arial', 9, 'bold')).grid(row=0, column=4)
        
        # Variables para los checkboxes
        check_vars = []
        
        for i, mov in enumerate(movimientos):
            row_frame = ttk.Frame(scrollable_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            var = tk.BooleanVar(value=True)
            check_vars.append((var, mov))
            
            # Use original value from mov['valor'] and 'moneda'
            moneda = mov.get('moneda', 'COP')
            valor = mov['valor']
            desc = mov['descripcion']
            fecha = mov['fecha'].strftime('%Y-%m-%d')
            
            chk = ttk.Checkbutton(row_frame, variable=var)
            chk.grid(row=0, column=0, padx=5)
            
            ttk.Label(row_frame, text=fecha, width=12).grid(row=0, column=1)
            ttk.Label(row_frame, text=moneda, width=8).grid(row=0, column=2)
            ttk.Label(row_frame, text=f"{valor:,.2f}", width=15).grid(row=0, column=3)
            ttk.Label(row_frame, text=desc, width=60, anchor="w").grid(row=0, column=4, sticky="w")
            
        # Botones inferiores
        bottom_frame = ttk.Frame(dlg, padding=10)
        bottom_frame.pack(fill=tk.X)
        
        result_container = {'seleccionados': None}
        
        def seleccionar_todos(valor):
            for var, _ in check_vars:
                var.set(valor)
                
        def cancelar():
            dlg.destroy()
            
        def aceptar():
            seleccionados = [m for v, m in check_vars if v.get()]
            result_container['seleccionados'] = seleccionados
            dlg.destroy()
            
        ttk.Button(bottom_frame, text="Seleccionar Todos", command=lambda: seleccionar_todos(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Deseleccionar Todos", command=lambda: seleccionar_todos(False)).pack(side=tk.LEFT, padx=5)
        
        ttk.Frame(bottom_frame).pack(side=tk.LEFT, expand=True) # Spacer
        
        ttk.Button(bottom_frame, text="Cancelar", command=cancelar).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Cargar Seleccionados", command=aceptar).pack(side=tk.RIGHT, padx=5)
        
        self._centrar_caja_dialogo(dlg, 900, 600)
        self.root.wait_window(dlg)
        
        return result_container['seleccionados']
    
    def agregar_log(self, mensaje, tipo='info'):
        """Agrega un mensaje al log con timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {mensaje}\n", tipo)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
    
    def seleccionar_archivo(self):
        """Abre un diálogo para seleccionar el archivo PDF."""
        cuenta = self.cuenta_seleccionada.get()
        config = CUENTAS_CONFIG[cuenta]
        
        if config['extractor'] is None:
            self.mostrar_mensaje_custom("No Disponible", 
                                  f"El extractor para '{cuenta}' aún no está implementado.", 'warning')
            return
        
        archivo = filedialog.askopenfilename(
            title=f"Seleccionar Archivo de {cuenta}",
            filetypes=config['file_filter'],
            initialdir=os.path.join(os.getcwd(), "MovimientosPendientes"),
            parent=self.root
        )
        
        if archivo:
            self.archivo_pdf = archivo
            nombre_archivo = os.path.basename(archivo)
            self.file_label.config(text=nombre_archivo, foreground='black', font=('Arial', 9, 'bold'))
            self.agregar_log(f"✓ Archivo seleccionado: {nombre_archivo}", 'success')
            
            # Extraer y mostrar preview
            self.extraer_y_mostrar()
    
    def extraer_y_mostrar(self):
        """Extrae movimientos del PDF y muestra preview."""
        self.agregar_log("📂 Extrayendo movimientos del archivo...", 'info')
        
        try:
            cuenta = self.cuenta_seleccionada.get()
            config = CUENTAS_CONFIG[cuenta]
            extractor = config['extractor']
            
            # Extraer movimientos
            self.movimientos_extraidos = extractor(self.archivo_pdf)
            
            if not self.movimientos_extraidos:
                self.agregar_log("⚠ No se encontraron movimientos en el archivo", 'warning')
                return
            
            # Mostrar estadísticas
            stats = obtener_estadisticas(self.movimientos_extraidos)
            self.agregar_log(f"✓ Extraídos {stats['total']} movimientos " +
                           f"({stats['debitos']} débitos, {stats['creditos']} créditos)", 'success')
            
            # Mostrar preview inicial con todos los movimientos
            self.actualizar_preview_todos()
            
            # Ejecutar validación automáticamente
            self.validar_duplicados()
            
        except Exception as e:
            self.agregar_log(f"✗ Error al extraer movimientos: {e}", 'error')
            import traceback
            traceback.print_exc()
    
    def validar_duplicados(self):
        """Valida qué movimientos ya existen en la base de datos."""
        if not self.movimientos_extraidos:
            self.mostrar_mensaje_custom("Advertencia", "No hay movimientos para validar.", 'warning')
            return
        
        self.agregar_log("🔍 Validando duplicados contra la base de datos...", 'info')
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=self._ejecutar_validacion)
        thread.daemon = True
        thread.start()
    
    def _ejecutar_validacion(self):
        """Ejecuta la validación de duplicados en background."""
        try:
            # Conectar a la base de datos
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cuenta = self.cuenta_seleccionada.get()
            cuenta_id = CUENTAS_CONFIG[cuenta]['account_id']
            
            # Obtener TerceroID de Bancolombia para validación consistente
            contactid_bancolombia = obtener_contactid_bancolombia(cursor)
            
            self.movimientos_nuevos = []
            self.movimientos_duplicados = []
            
            # Validar cada movimiento
            for mov in self.movimientos_extraidos:
                # Aplicar las MISMAS transformaciones que se usan durante la carga
                es_cuota_manejo = detectar_cuota_manejo(mov['descripcion'])
                
                if es_cuota_manejo and contactid_bancolombia:
                    descripcion_a_buscar = 'Bancolombia'
                    referencia_a_buscar = 'Cuota de Manejo'
                else:
                    descripcion_a_buscar = mov['descripcion'].title()
                    referencia_a_buscar = mov['referencia'] if mov['referencia'] else ''
                
                # Query para buscar duplicados: Fecha + Descripción + Referencia + Valor
                # Si tenemos moneda, también podríamos validar cuenta, pero por ahora mantengamos simple
                cursor.execute("""
                    SELECT COUNT(*) FROM movimientos
                    WHERE (CuentaID = %s OR CuentaID = %s)
                      AND Fecha = %s
                      AND Descripcion = %s
                      AND Referencia = %s
                      AND Valor = %s
                """, (cuenta_id, 5 if cuenta_id == 4 else cuenta_id, mov['fecha'].date(), descripcion_a_buscar, referencia_a_buscar, mov['valor']))
                
                count = cursor.fetchone()[0]
                
                if count > 0:
                    self.movimientos_duplicados.append(mov)
                    # Log detallado del duplicado encontrado (solo primeros 5)
                    if len(self.movimientos_duplicados) <= 5:
                        self.agregar_log(
                            f"  → Duplicado: {mov['fecha'].strftime('%Y-%m-%d')} | " +
                            f"{descripcion_a_buscar[:30]} | ${mov['valor']:,.2f}", 
                            'warning'
                        )
                else:
                    self.movimientos_nuevos.append(mov)
            
            cursor.close()
            conn.close()
            
            # Mostrar resultados
            self.mostrar_resultados_validacion()
            
            # Actualizar estadísticas visuales
            self.actualizar_estadisticas_visuales()
            
        except Exception as e:
            self.agregar_log(f"✗ Error al validar duplicados: {e}", 'error')
            import traceback
            traceback.print_exc()
    
    def mostrar_resultados_validacion(self):
        """Muestra los resultados de la validación en el área de validación."""
        self.validation_text.delete('1.0', tk.END)
        
        total = len(self.movimientos_extraidos)
        nuevos = len(self.movimientos_nuevos)
        duplicados = len(self.movimientos_duplicados)
        
        resultado = f"""
╔══════════════════════════════════════════════════════════════════╗
║           RESULTADOS DE VALIDACIÓN DE DUPLICADOS                 ║
╠══════════════════════════════════════════════════════════════════╣
║  Total de movimientos en archivo:    {total:>5}                       ║
║  Registros NUEVOS (no en BD):        {nuevos:>5}  ✓                   ║
║  Registros DUPLICADOS (ya en BD):    {duplicados:>5}  ⚠                   ║
╚══════════════════════════════════════════════════════════════════╝
"""
        
        # Si hay duplicados, mostrar detalles
        if duplicados > 0:
            resultado += "\n⚠ MOVIMIENTOS DUPLICADOS (ya existen en la base de datos):\n"
            resultado += "-" * 70 + "\n"
            for i, mov in enumerate(self.movimientos_duplicados[:10], 1):
                resultado += f"{i}. {mov['fecha'].strftime('%Y-%m-%d')} | "
                resultado += f"{mov['descripcion'][:35]:<35} | "
                resultado += f"${mov['valor']:>12,.2f}\n"
            
            if duplicados > 10:
                resultado += f"\n... y {duplicados - 10} duplicados más.\n"
        
        self.validation_text.insert('1.0', resultado)
        
        if duplicados > 0:
            self.agregar_log(f"⚠ Se encontraron {duplicados} movimientos duplicados (ver detalles arriba)", 'warning')
            self.agregar_log(f"  → Estos registros NO se cargarán nuevamente", 'warning')
        
        if nuevos > 0:
            self.agregar_log(f"✓ {nuevos} movimientos nuevos listos para cargar", 'success')
            self.load_button.config(state='normal')
        else:
            self.agregar_log("ℹ No hay movimientos nuevos para cargar", 'info')
            self.load_button.config(state='disabled')
    
    def actualizar_preview_todos(self):
        """Actualiza el preview para mostrar TODOS los movimientos extraídos."""
        # Limpiar preview
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        if not self.movimientos_extraidos:
            return
        
        # Ordenar movimientos por fecha (más antiguos primero)
        movimientos_ordenados = sorted(self.movimientos_extraidos, key=lambda x: x['fecha'])
        
        # Mostrar primeros 20 movimientos ordenados
        for mov in movimientos_ordenados[:20]:
            self.preview_tree.insert('', 'end', values=(
                mov['fecha'].strftime('%Y-%m-%d'),
                mov['descripcion'][:60],  # Truncar descripción
                mov['referencia'] if mov['referencia'] else '',
                f"${mov['valor']:,.2f}"
            ))
        
        if len(movimientos_ordenados) > 20:
            self.agregar_log(f"  (Preview mostrando primeros 20 de {len(movimientos_ordenados)} movimientos)", 'info')
    
    def actualizar_estadisticas_visuales(self):
        """Actualiza las cajas de estadísticas visuales."""
        total = len(self.movimientos_extraidos)
        duplicados = len(self.movimientos_duplicados)
        nuevos = len(self.movimientos_nuevos)
        
        self.stats_leidos.config(text=str(total))
        self.stats_duplicados.config(text=str(duplicados))
        self.stats_a_cargar.config(text=str(nuevos))
    
    def cargar_registros(self):
        """Carga los registros nuevos a la base de datos."""
        if not self.movimientos_nuevos:
            self.mostrar_mensaje_custom("Advertencia", "No hay movimientos nuevos para cargar.", 'warning')
            return
        
        # Mostrar diálogo de selección para TODAS las cuentas
        seleccionados = self.mostrar_dialogo_seleccion(self.movimientos_nuevos)
        
        # Si se canceló el diálogo
        if seleccionados is None:
            self.agregar_log("⚠ Selección cancelada por el usuario", 'warning')
            return
        
        # Si no se seleccionó ningún movimiento
        if not seleccionados:
            self.agregar_log("⚠ No se seleccionaron movimientos para cargar", 'warning')
            return
        
        # Actualizar lista con la selección
        self.movimientos_nuevos = seleccionados
        cuenta_actual = self.cuenta_seleccionada.get()
        
        self.agregar_log(f"📤 Iniciando carga de {len(self.movimientos_nuevos)} movimientos...", 'info')
        self.load_button.config(state='disabled')
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=self._ejecutar_carga)
        thread.daemon = True
        thread.start()
    
    def _ejecutar_carga(self):
        """Ejecuta la carga de registros en background."""
        conn = None
        try:
            # Conectar a la base de datos
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cuenta = self.cuenta_seleccionada.get()
            cuenta_id = CUENTAS_CONFIG[cuenta]['account_id']
            
            # Obtener TerceroID de Bancolombia para cuotas de manejo
            contactid_bancolombia = obtener_contactid_bancolombia(cursor)
            if contactid_bancolombia:
                self.agregar_log(f"✓ TerceroID Bancolombia encontrado: {contactid_bancolombia}", 'success')
                self.agregar_log("  → Cuotas de manejo se mapearán automáticamente", 'info')
            else:
                self.agregar_log("⚠ TerceroID Bancolombia no encontrado. Cuotas de manejo se insertarán sin contacto.", 'warning')
            
            # Commit para asegurar que la transacción esté limpia antes de los INSERTs
            conn.commit()
            
            sql_insert = """
                INSERT INTO movimientos 
                (Fecha, Descripcion, Referencia, Valor, USD, TRM, 
                 MonedaID, CuentaID, TerceroID, GrupoID, ConceptoID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            total = len(self.movimientos_nuevos)
            cargados = 0
            errores = 0
            cuotas_manejo_detectadas = 0
            
            self.progress_bar['maximum'] = total
            self.progress_bar['value'] = 0
            
            # Ordenar movimientos por fecha (más antiguos primero)
            movimientos_ordenados = sorted(self.movimientos_nuevos, key=lambda x: x['fecha'])
            
            for i, mov in enumerate(movimientos_ordenados, 1):
                try:
                    # Lógica de Moneda y Cuenta Dinámica
                    target_cuenta_id = cuenta_id
                    valor_final = mov['valor']
                    
                    if 'moneda' in mov:
                        # Lógica específica para Tarjeta de Crédito (PDF incluye ambos)
                        trm_value = 0  # Default TRM to 0 for all credit card movements
                        moneda_id = 1  # Según requerimiento: siempre será Pesos (Id 1)
                        
                        if mov['moneda'] == 'COP':
                            valor_final = mov['valor'] * -1
                            usd_value = 0
                            # Si estamos cargando como TC (4 o 5), forzar a 4 (Pesos)
                            if cuenta_id in [4, 5]:
                                target_cuenta_id = 4
                        elif mov['moneda'] == 'USD':
                            valor_final = 0 # Valor en 0 hasta que se defina TRM
                            usd_value = mov['valor'] * -1
                            # Si estamos cargando como TC (4 o 5), forzar a 5 (Dolares)
                            if cuenta_id in [4, 5]:
                                target_cuenta_id = 5
                        else:
                            usd_value = 0
                    else:
                        # Lógica legacy para Ahorros/Fondo
                        if cuenta_id in [2, 3]:
                            moneda_id = 1
                            usd_value = 0
                            trm_value = 0
                        else:
                            moneda_id = None
                            usd_value = None
                            trm_value = None
                    
                    # Detectar si es cuota de manejo
                    es_cuota_manejo = detectar_cuota_manejo(mov['descripcion'])
                    
                    # Determinar TerceroID, descripción y referencia
                    if es_cuota_manejo and contactid_bancolombia:
                        contact_id = contactid_bancolombia
                        descripcion = 'Bancolombia'
                        referencia = 'Cuota de Manejo'
                        cuotas_manejo_detectadas += 1
                    else:
                        contact_id = None
                        descripcion = mov['descripcion'].title()
                        referencia = mov['referencia'] if mov['referencia'] else ''
                    
                    cursor.execute(sql_insert, (
                        mov['fecha'].date(),
                        descripcion,
                        referencia,
                        valor_final,
                        usd_value,  # USD
                        trm_value,  # TRM
                        moneda_id,  # MonedaID (Siempre 1 para TC)
                        target_cuenta_id,
                        contact_id,  # TerceroID - Bancolombia si es cuota de manejo, NULL si no
                        None,  # GrupoID - NULL
                        None   # ConceptoID - NULL
                    ))
                    
                    # Commit individual para cada registro
                    conn.commit()
                    cargados += 1
                    
                except Exception as e:
                    # Rollback automático en caso de error
                    conn.rollback()
                    errores += 1
                    
                    # Log detallado del error
                    error_msg = f"✗ Error en registro {i}: {str(e)}"
                    self.agregar_log(error_msg, 'error')
                    self.agregar_log(f"  → Fecha: {mov['fecha'].strftime('%Y-%m-%d')}, Desc: {mov['descripcion'][:40]}, Valor: {mov['valor']}", 'error')
                
                # Actualizar progreso
                self.progress_bar['value'] = i
                if i % 10 == 0 or i == total:
                    self.root.update_idletasks()
            
            cursor.close()
            conn.close()
            
            # Mostrar resultados
            if errores == 0:
                self.agregar_log(f"✓✓✓ CARGA COMPLETADA EXITOSAMENTE ✓✓✓", 'success')
                self.agregar_log(f"✓ {cargados} movimientos cargados correctamente", 'success')
                if cuotas_manejo_detectadas > 0:
                    self.agregar_log(f"✓ {cuotas_manejo_detectadas} cuotas de manejo mapeadas automáticamente a Bancolombia", 'success')
                self.mostrar_mensaje_custom("Éxito", 
                                   f"Se cargaron {cargados} movimientos exitosamente.\n" +
                                   (f"{cuotas_manejo_detectadas} cuotas de manejo mapeadas a Bancolombia." if cuotas_manejo_detectadas > 0 else ""),
                                   'success')
            else:
                self.agregar_log(f"⚠ Carga completada con {errores} errores", 'warning')
                self.agregar_log(f"✓ {cargados} movimientos cargados, {errores} errores", 'warning')
                if cuotas_manejo_detectadas > 0:
                    self.agregar_log(f"✓ {cuotas_manejo_detectadas} cuotas de manejo mapeadas automáticamente a Bancolombia", 'success')
                self.mostrar_mensaje_custom("Completado con errores",
                                      f"Se cargaron {cargados} movimientos.\n{errores} registros tuvieron errores.", 'warning')
            
            # Resetear
            self.progress_bar['value'] = 0
            
        except Exception as e:
            self.agregar_log(f"✗ Error crítico durante la carga: {e}", 'error')
            self.mostrar_mensaje_custom("Error", f"Error durante la carga:\n{e}", 'error')
            import traceback
            traceback.print_exc()
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
            self.load_button.config(state='normal')
    
    def limpiar_todo(self):
        """Limpia todos los datos y resetea la interfaz."""
        self.archivo_pdf = None
        self.movimientos_extraidos = []
        self.movimientos_nuevos = []
        self.movimientos_duplicados = []
        
        self.file_label.config(text="Ningún archivo seleccionado", foreground='gray', font=('Arial', 9))
        
        # Limpiar estadísticas visuales
        self.stats_leidos.config(text="0")
        self.stats_duplicados.config(text="0")
        self.stats_a_cargar.config(text="0")
        
        # Limpiar preview
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # Limpiar validación
        self.validation_text.delete('1.0', tk.END)
        
        # Limpiar log
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
        
        # Resetear botones
        self.load_button.config(state='disabled')
        self.progress_bar['value'] = 0
        
        self.agregar_log("✓ Interfaz limpiada", 'success')
        self.agregar_log("📁 Selecciona una cuenta y un archivo PDF para comenzar", 'info')


def main():
    """Función principal."""
    root = tk.Tk()
    app = CargadorMovimientosGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
