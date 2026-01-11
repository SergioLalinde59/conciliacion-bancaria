#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Movimientos por Clasificar - Interfaz Gráfica
Permite asignar terceros, grupos y conceptos a movimientos bancarios pendientes.

Autor: Antigravity
Fecha: 2025-12-30
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import psycopg2
from datetime import datetime
import re
from thefuzz import fuzz

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}


class AsignarClasificacionGUI:
    # Definición de reglas de negocio
    REGLAS = [
        {
            'patron': 'Abono Intereses Ahorros', # String para búsqueda ILIKE
            'tid': 19, 'gid': 4, 'cid': 23
        },
        {
            'patron': 'Impto Gobierno', # Cubre "Impto Gobierno 4x100" y 4x1000
            'tid': 45, 'gid': 22, 'cid': 117
        },
        {
            'patron': 'Traslado De Fondo', # Cubre "Traslado De Fondo De..."
            'tid': 76, 'gid': 47, 'cid': 399
        }
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Movimientos por Clasificar")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        
        # Variables de estado
        self.movimientos_pendientes = []
        self.movimiento_actual = None
        self.contexto_historico = []
        self.tercero_seleccionado_id = None
        self.grupo_seleccionado_id = None
        self.tercero_seleccionado_id = None
        self.grupo_seleccionado_id = None
        self.concepto_seleccionado_id = None
        self.regla_actual = None  # Almacena la regla detectada para el movimiento actual
        
        # Filtro de Cuenta
        self.cuenta_filtro_id = None
        
        # Variables UI para editor
        self.grupo_combo = None
        self.concepto_combo = None
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
        # Log inicial
        self.agregar_log("✓ Aplicación iniciada correctamente", 'success')
        self.agregar_log("📋 Cargando movimientos pendientes...", 'info')
        
        # Cargar movimientos pendientes al inicio
        self.cargar_movimientos_pendientes()
    
    def setup_ui(self):
        """Configura la interfaz de usuario con 3 secciones."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)  # Pendientes
        main_frame.rowconfigure(3, weight=1)  # Contexto
        main_frame.rowconfigure(5, weight=2)  # Editor
        main_frame.rowconfigure(7, weight=1)  # Log
        
        # Título
        title_label = ttk.Label(main_frame, text="Movimientos por Clasificar", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # === SECCIÓN 1: Movimientos Pendientes (Tercio Superior) ===
        self.setup_seccion_pendientes(main_frame, row=1)
        
        # === SECCIÓN 2: Contexto Histórico (Tercio Medio) ===
        self.setup_seccion_contexto(main_frame, row=3)
        
        # === SECCIÓN 2: Contexto Histórico (Resto del espacio) ===
        self.setup_seccion_contexto(main_frame, row=3, weight=2)
        
        # === Log de Eventos ===
        self.setup_log(main_frame, row=7)
    
    def setup_seccion_pendientes(self, parent, row):
        """Configura la sección de movimientos pendientes."""
        frame = ttk.LabelFrame(parent, text="1. Movimientos Pendientes de Clasificación", padding="10")
        frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)  # TreeView
        
        # Frame de Filtros
        filter_frame = ttk.Frame(frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(filter_frame, text="Filtrar por Cuenta:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.cuenta_filtro_combo = ttk.Combobox(filter_frame, state="readonly", width=30)
        self.cuenta_filtro_combo.pack(side=tk.LEFT)
        self.cuenta_filtro_combo.bind('<<ComboboxSelected>>', self.on_cuenta_filtro_changed)
        
        # Cargar cuentas para filtro
        self.cargar_cuentas_filtro()
        
        # Contador de pendientes
        self.lbl_contador = ttk.Label(frame, text="Movimientos por revisar: 0", 
                                     font=('Arial', 10, 'bold'), foreground='blue')
        self.lbl_contador.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # TreeView para movimientos pendientes
        columns = ('id', 'fecha', 'descripcion', 'referencia', 'valor', 'usd', 'faltante', 'cuenta')
        self.pendientes_tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
        
        self.pendientes_tree.heading('id', text='ID')
        self.pendientes_tree.heading('fecha', text='Fecha')
        self.pendientes_tree.heading('descripcion', text='Descripción')
        self.pendientes_tree.heading('referencia', text='Referencia')
        self.pendientes_tree.heading('valor', text='Valor (COP)')
        self.pendientes_tree.heading('usd', text='USD')
        self.pendientes_tree.heading('faltante', text='Faltante')
        self.pendientes_tree.heading('cuenta', text='Cuenta')
        
        self.pendientes_tree.column('id', width=50)
        self.pendientes_tree.column('fecha', width=90)
        self.pendientes_tree.column('descripcion', width=300)
        self.pendientes_tree.column('referencia', width=120)
        self.pendientes_tree.column('valor', width=100, anchor='e')
        self.pendientes_tree.column('usd', width=80, anchor='e')
        self.pendientes_tree.column('faltante', width=120)
        self.pendientes_tree.column('cuenta', width=120)
        
        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.pendientes_tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.pendientes_tree.xview)
        self.pendientes_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.pendientes_tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=2, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        # Bind para selección
        self.pendientes_tree.bind('<Double-Button-1>', self.seleccionar_movimiento)
        
        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, pady=(10, 0))
        
        self.refresh_button = ttk.Button(btn_frame, text="🔄 Actualizar Lista", 
                                        command=self.cargar_movimientos_pendientes, width=20)
        self.refresh_button.grid(row=0, column=0, padx=5)
    
    def setup_seccion_contexto(self, parent, row, weight=1):
        """Configura la sección de contexto histórico."""
        frame = ttk.LabelFrame(parent, text="2. Contexto: Últimos 5 Movimientos Completos", padding="10")
        frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=weight)
        
        # TreeView para contexto
        columns = ('fecha', 'descripcion', 'referencia', 'valor', 'tercero', 'grupo', 'concepto')
        self.contexto_tree = ttk.Treeview(frame, columns=columns, show='headings', height=5)
        
        self.contexto_tree.heading('fecha', text='Fecha')
        self.contexto_tree.heading('descripcion', text='Descripción')
        self.contexto_tree.heading('referencia', text='Referencia')
        self.contexto_tree.heading('valor', text='Valor')
        self.contexto_tree.heading('tercero', text='Tercero')
        self.contexto_tree.heading('grupo', text='Grupo')
        self.contexto_tree.heading('concepto', text='Concepto')
        
        self.contexto_tree.column('fecha', width=100)
        self.contexto_tree.column('descripcion', width=300)
        self.contexto_tree.column('referencia', width=150)
        self.contexto_tree.column('valor', width=100, anchor='e')
        self.contexto_tree.column('tercero', width=200)
        self.contexto_tree.column('grupo', width=150)
        self.contexto_tree.column('concepto', width=200)
        
        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.contexto_tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.contexto_tree.xview)
        self.contexto_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.contexto_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind doble clic
        self.contexto_tree.bind("<Double-1>", self.seleccionar_desde_contexto)
    
    # setup_seccion_editor ELIMINADO en favor de modal
    
    def setup_log(self, parent, row):
        """Configura el área de log."""
        log_frame = ttk.LabelFrame(parent, text="Log de Eventos", padding="5")
        log_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80, 
                                                   font=('Courier', 9), state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar colores
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('info', foreground='blue')
    
    def agregar_log(self, mensaje, tipo='info'):
        """Agrega un mensaje al log con timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {mensaje}\n", tipo)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
    
    def cargar_cuentas_filtro(self):
        """Carga las cuentas disponibles para el filtro."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT cuentaid, cuenta FROM cuentas ORDER BY cuenta")
            cuentas = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Formato: "ID: Nombre"
            self.cuentas_filtro_map = {f"{c[0]}: {c[1]}": c[0] for c in cuentas}
            valores = ["Todos"] + list(self.cuentas_filtro_map.keys())
            self.cuenta_filtro_combo['values'] = valores
            self.cuenta_filtro_combo.current(0)  # Seleccionar "Todos" por defecto
            
        except Exception as e:
            self.agregar_log(f"✗ Error al cargar cuentas: {e}", 'error')

    def on_cuenta_filtro_changed(self, event):
        """Maneja el cambio de filtro de cuenta."""
        seleccion = self.cuenta_filtro_combo.get()
        if seleccion == "Todos":
            self.cuenta_filtro_id = None
        else:
            self.cuenta_filtro_id = self.cuentas_filtro_map.get(seleccion)
            
        self.cargar_movimientos_pendientes()

    def cargar_movimientos_pendientes(self):
        """Carga los movimientos que faltan tercero, grupo o concepto."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Construir query dinámica
            sql = """
                SELECT m.Id, m.Fecha, m.Descripcion, m.Referencia, m.Valor, m.USD,
                       m.TerceroID, m.GrupoID, m.ConceptoID, c.cuenta
                FROM movimientos m
                LEFT JOIN cuentas c ON m.CuentaID = c.cuentaid
                WHERE (m.TerceroID IS NULL 
                   OR m.GrupoID IS NULL 
                   OR m.ConceptoID IS NULL)
            """
            
            params = []
            if self.cuenta_filtro_id:
                sql += " AND m.CuentaID = %s"
                params.append(self.cuenta_filtro_id)
                
            sql += " ORDER BY m.Fecha ASC LIMIT 100"
            
            cursor.execute(sql, tuple(params))
            
            self.movimientos_pendientes = cursor.fetchall()
            
            # Limpiar TreeView
            for item in self.pendientes_tree.get_children():
                self.pendientes_tree.delete(item)
            
            # Poblar TreeView
            for mov in self.movimientos_pendientes:
                mov_id, fecha, desc, ref, valor, usd, tercero_id, grupo_id, concepto_id, cuenta_nombre = mov
                
                # Determinar qué falta
                faltantes = []
                if tercero_id is None:
                    faltantes.append("Tercero")
                if grupo_id is None:
                    faltantes.append("Grupo")
                if concepto_id is None:
                    faltantes.append("Concepto")
                
                faltante_str = ", ".join(faltantes)
                
                self.pendientes_tree.insert('', 'end', values=(
                    mov_id,
                    fecha.strftime('%Y-%m-%d'),
                    desc[:50],
                    ref if ref else '',
                    f"${valor:,.2f}",
                    f"${usd:,.2f}" if usd else '$0.00',
                    faltante_str,
                    cuenta_nombre if cuenta_nombre else ""
                ))
            
            cursor.close()
            conn.close()
            
            # Actualizar contador
            self.lbl_contador.config(text=f"Movimientos por revisar: {len(self.movimientos_pendientes)}")
            
            self.agregar_log(f"✓ Cargados {len(self.movimientos_pendientes)} movimientos pendientes", 'success')
            
        except Exception as e:
            self.agregar_log(f"✗ Error al cargar movimientos: {e}", 'error')
    
    def seleccionar_movimiento(self, event):
        """Maneja la selección de un movimiento pendiente."""
        selection = self.pendientes_tree.selection()
        if not selection:
            return
        
        item = self.pendientes_tree.item(selection[0])
        mov_id = item['values'][0]
        
        self.agregar_log(f"📝 Abriendo editor para movimiento ID={mov_id}", 'info')
        
        # Cargar datos y abrir modal
        self.abrir_editor_modal(mov_id)

    def abrir_editor_modal(self, mov_id):
        """Abre una ventana modal para editar el movimiento."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Fecha, Descripcion, Referencia, Valor, TerceroID, GrupoID, ConceptoID, Detalle FROM movimientos WHERE Id = %s", (mov_id,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el movimiento: {e}")
            return

        if not data:
            return
            
        self.movimiento_actual = data
        
        # Crear ventana modal
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar Movimiento #{data[0]}")
        self.current_dialog = dialog # Referencia para cerrar después
        
        # Dimensiones del modal
        d_width = 900
        d_height = 550
        
        # Forzar actualización de la ventana principal para obtener dimensiones correctas
        self.root.update_idletasks()
        
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        
        # Centrado horizontalmente con respecto a la ventana principal
        pos_x = root_x + (root_w // 2) - (d_width // 2)
        
        # Posicionamiento vertical: distancia fija desde el borde superior de la pantalla
        # Esto deja espacio debajo para ver la sección de contexto histórico
        margen_superior = 50  # 50 pixels desde el borde superior de la pantalla
        pos_y = margen_superior
        
        dialog.geometry(f"{d_width}x{d_height}+{pos_x}+{pos_y}")
        dialog.transient(self.root)
        dialog.grab_set() # Modalidad
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Botones (Crear primero para que existan referencias) ---
        btn_frame = ttk.Frame(frame, padding="10")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        self.update_button = ttk.Button(btn_frame, text="✓ Actualizar Movimiento", command=self.actualizar_registro, state='disabled')
        self.update_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        self.btn_batch_update = ttk.Button(btn_frame, text="⚡ Aplicar a Todos", command=self.actualizar_lote, state='disabled')
        self.btn_batch_update.pack(side=tk.RIGHT, padx=5)
        
        # --- Información del Movimiento (ReadOnly) ---
        info_frame = ttk.LabelFrame(frame, text="Información del Movimiento", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Fila 1 Info
        ttk.Label(info_frame, text="Fecha:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=str(data[1])).grid(row=0, column=1, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(info_frame, text="Referencia:", font=('Arial', 9, 'bold')).grid(row=0, column=2, sticky=tk.W)
        ttk.Label(info_frame, text=data[3] if data[3] else "").grid(row=0, column=3, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(info_frame, text="Valor:", font=('Arial', 9, 'bold')).grid(row=0, column=4, sticky=tk.W)
        ttk.Label(info_frame, text=f"${data[4]:,.2f}").grid(row=0, column=5, sticky=tk.W, padx=(5, 20))
        
        # Fila 2 Descripción
        ttk.Label(info_frame, text="Descripción:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(info_frame, text=data[2]).grid(row=1, column=1, columnspan=5, sticky=tk.W, padx=5)

        # Labels de Patrón
        self.lbl_patron = ttk.Label(info_frame, text="", foreground='blue', font=('Arial', 8, 'bold'))
        self.lbl_patron.grid(row=2, column=0, columnspan=6, sticky=tk.W, pady=(5,0))
        
        # Lógica de detección de patrón y contexto (para cargar contexto aunque no se muestre interactivo acá)
        patron_ref = self.detectar_patron_referencia(data[3])
        if patron_ref == 'celular':
             self.lbl_patron.config(text="📱 Celular detectado en referencia")
        elif patron_ref == 'cuenta':
             self.lbl_patron.config(text="🏦 Cuenta bancaria detectada en referencia")
        
        # Detectar regla automática
        # Detectar regla automática
        self.regla_actual = self.detectar_regla(data[2])
        # self.cargar_contexto_historico... MOVIDO ABAJO para que existan los combos

        # --- Clasificación ---
        class_frame = ttk.LabelFrame(frame, text="Clasificación", padding="10")
        class_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Tercero
        ttk.Label(class_frame, text="Tercero:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.tercero_combo = ttk.Combobox(class_frame, width=50) # Bind to self to reuse ID selection methods
        self.tercero_combo.grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        self.tercero_combo.bind('<<ComboboxSelected>>', self.on_tercero_seleccionado)
        self.tercero_combo.bind('<Return>', lambda e: self.seleccionar_por_id(self.tercero_combo))
        
        self.btn_crear_tercero = ttk.Button(class_frame, text="+ Nuevo", command=self.crear_nuevo_tercero)
        self.btn_crear_tercero.grid(row=0, column=3, padx=5)
        
        # Grupo y Concepto
        ttk.Label(class_frame, text="Grupo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.grupo_combo = ttk.Combobox(class_frame, width=30)
        self.grupo_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.grupo_combo.bind('<<ComboboxSelected>>', self.on_grupo_seleccionado)
        self.grupo_combo.bind('<Return>', lambda e: self.seleccionar_por_id(self.grupo_combo))
        
        ttk.Label(class_frame, text="Concepto:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.concepto_combo = ttk.Combobox(class_frame, width=30)
        self.concepto_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        self.concepto_combo.bind('<<ComboboxSelected>>', self.on_concepto_seleccionado)
        self.concepto_combo.bind('<Return>', lambda e: self.seleccionar_por_id(self.concepto_combo))

        # Labels de sugerencia (Feedback)
        self.lbl_grupo_sugerido = ttk.Label(class_frame, text="", font=('Arial', 8), foreground='green')
        self.lbl_grupo_sugerido.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        self.lbl_concepto_sugerido = ttk.Label(class_frame, text="", font=('Arial', 8), foreground='green')
        self.lbl_concepto_sugerido.grid(row=2, column=3, sticky=tk.W, padx=5)

        # Detalle
        ttk.Label(class_frame, text="Detalle/Notas:").grid(row=3, column=0, sticky=tk.W, pady=10)
        self.txt_detalle = ttk.Entry(class_frame, width=80)
        self.txt_detalle.grid(row=3, column=1, columnspan=3, sticky=tk.W, padx=5)
        if data[8]: self.txt_detalle.insert(0, data[8])
        
        # Cargar contexto histórico AHORA que los combos existen
        # (Esto puede setear valores en los combos si encuentra reglas)
        self.cargar_contexto_historico(data[1], data[3], patron_ref, data[5], data[6], data[7]) 

        # Configure Combos Data
        self.cargar_terceros_para_busqueda() # Repopulate third combos
        # Set values if exist
        if data[5]: # TerceroID
            # Asignar valor al combo (buscando en values)
            t_val = next((t for t in self.tercero_combo['values'] if t.startswith(f"{data[5]}:")), "")
            self.tercero_combo.set(t_val)
            self.tercero_seleccionado_id = data[5]
        else:
             self.tercero_seleccionado_id = None
             
        # Groups and Concepts setup
        # Re-use setup_filtering logic on these new widgets
        self.setup_filtering(self.tercero_combo, self.tercero_combo['values'])
        self.setup_filtering(self.grupo_combo, self.lista_grupos_formato)
        
        # Conceptos logic
        def get_conceptos_validos():
            if self.grupo_seleccionado_id:
                 return [f"{cid}: {nombre}" for cid, nombre, gid in self.conceptos_completos if gid == self.grupo_seleccionado_id]
            else:
                 return [f"{cid}: {nombre}" for cid, nombre, gid in self.conceptos_completos]
        self.setup_filtering(self.concepto_combo, get_conceptos_validos)
        
        if data[6]: # GrupoID
             g_val = next((g for g in self.lista_grupos_formato if g.startswith(f"{data[6]}:")), "")
             self.grupo_combo.set(g_val)
             self.grupo_seleccionado_id = data[6]
             self.on_grupo_seleccionado(None) # Filter concepts
        
        if data[7]: # ConceptoID
             # Need to find in current concept list
             c_list = get_conceptos_validos()
             c_val = next((c for c in c_list if c.startswith(f"{data[7]}:")), "")
             self.concepto_combo.set(c_val)
             self.concepto_seleccionado_id = data[7]

        # --- Botones (Ya creados arriba) ---
        
        # Check for batch rule
        self.verificar_lote_automatico()

        # Check for batch rule
        self.verificar_lote_automatico() 

    # Reemplazo de funciones que usaban grid_forget/pack de la UI anterior
    def mostrar_busqueda_tercero(self): pass # Ya no necesario en modal fijo
    def limpiar_editor(self): pass # Ya no necesario, se crea nuevo dialog

    # Ajuste en actualizar_registro para cerrar dialog
    def actualizar_registro(self):
        # Lógica original pero agregando cierre del modal
        if not self.movimiento_actual: return
        
        mov_id = self.movimiento_actual[0]
        detalle = self.txt_detalle.get().strip()
        
        tid = self.tercero_seleccionado_id
        gid = self.grupo_seleccionado_id
        cid = self.concepto_seleccionado_id
        
        # Validar combos si cambiaron manualmente sin seleccionar del dropdown
        # (La lógica de seleccionar_por_id y bindings maneja esto, confiamos en self.*_seleccionado_id)
        # Pero si el usuario borra el texto, deberíamos limpiar el ID
        t_text = self.tercero_combo.get().strip()
        g_text = self.grupo_combo.get().strip()
        c_text = self.concepto_combo.get().strip()
        
        if not t_text: tid = None
        if not g_text: gid = None
        if not c_text: cid = None
        
        # Intento de rescate de IDs desde el texto si no están seteados
        if tid is None and t_text and ':' in t_text:
             try: tid = int(t_text.split(':')[0])
             except: pass
        
        if gid is None and g_text and ':' in g_text:
             try: gid = int(g_text.split(':')[0])
             except: pass
             
        if cid is None and c_text and ':' in c_text:
             try: cid = int(c_text.split(':')[0])
             except: pass

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE movimientos
                SET TerceroID = %s, GrupoID = %s, ConceptoID = %s, Detalle = %s
                WHERE Id = %s
            """, (tid, gid, cid, detalle, mov_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.agregar_log(f"✓ Movimiento ID={mov_id} actualizado.", 'success')
            
            # Cerrar modal
            if hasattr(self, 'current_dialog'):
                self.current_dialog.destroy()
            
            # Recargar pendientes
            self.cargar_movimientos_pendientes()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")
    
    def seleccionar_desde_contexto(self, event):
        """
        Al doble clic en contexto:
        1. Si hay un editor abierto, copia los datos a ese editor.
        2. Si no hay editor abierto (estamos en listado), abre el editor para el movimiento pendiente seleccionado
           PERO precargando los datos de este contexto.
        """
        selection = self.contexto_tree.selection()
        if not selection:
            return
        
        item = self.contexto_tree.item(selection[0])
        values = item['values']
        # values: date(0), desc(1), ref(2), val(3), tercero(4), grupo(5), concepto(6)
        
        tercero_str = values[4] # "ID-Nombre"
        grupo_str = values[5]
        concepto_str = values[6]
        
        # Helper para extraer ID
        def get_id_str(s): 
            return s.split('-')[0] if s and '-' in s else None
            
        tid = get_id_str(tercero_str)
        gid = get_id_str(grupo_str)
        cid = get_id_str(concepto_str)

        # Si tenemos un modal abierto (self.current_dialog existe y es valido)
        if hasattr(self, 'current_dialog') and self.current_dialog.winfo_exists():
            # Setear valores en los combos del modal
            if tid:
                 # Buscar valor completo en combo
                 val = next((v for v in self.tercero_combo['values'] if v.startswith(f"{tid}:")), "")
                 if val:
                     self.tercero_combo.set(val)
                     self.tercero_seleccionado_id = int(tid)
            
            if gid:
                 val = next((v for v in self.lista_grupos_formato if v.startswith(f"{gid}:")), "")
                 if val:
                     self.grupo_combo.set(val)
                     self.grupo_seleccionado_id = int(gid)
                     self.on_grupo_seleccionado(None) # Refrescar conceptos
            
            if cid:
                 # Buscar en conceptos validos actuales
                 val = next((v for v in self.concepto_combo['values'] if v.startswith(f"{cid}:")), "")
                 if val:
                     self.concepto_combo.set(val)
                     self.concepto_seleccionado_id = int(cid)
            
            self.agregar_log("✓ Datos copiados del contexto al editor.", 'success')
            
        else:
            # Si no hay modal abierto, abrimos modal del pendiente seleccionado, y aplicamos esto
            sel_pend = self.pendientes_tree.selection()
            if sel_pend:
                # Abrir primero
                self.seleccionar_movimiento(None)
                # Luego llamar recursivamente a esta función (ahora que el modal estará abierto)
                # Un pequeño delay para asegurar que el modal cargó
                self.root.after(200, lambda: self.seleccionar_desde_contexto(event))
            else:
                messagebox.showinfo("Información", "Seleccione primero un movimiento pendiente para aplicar estos datos.")

    # cargar_movimiento_completo REEMPLAZADO por lógica interna en abrir_editor_modal
    
    def detectar_patron_referencia(self, referencia):
        """Detecta si una referencia se asemeja a cuenta bancaria o celular."""
        if not referencia:
            return None
        
        # Limpiar string (solo dígitos)
        solo_digitos = ''.join(c for c in referencia if c.isdigit())
        
        # Celular colombiano: 10 dígitos, empieza con 3
        if len(solo_digitos) == 10 and solo_digitos[0] == '3':
            return 'celular'
        
        # Cuenta bancaria: 10-16 dígitos
        if 10 <= len(solo_digitos) <= 16:
            return 'cuenta'
        
        return None
    
    def cargar_contexto_historico(self, fecha_mov, referencia_mov, patron, tercero_id, grupo_id, concepto_id):
        """Carga los 5 registros anteriores completos."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            desc_mov = ""
            if self.movimiento_actual:
                desc_mov = self.movimiento_actual[2]
            
            # Detectar Regla al inicio
            self.regla_actual = self.detectar_regla(desc_mov)
            
            # Estrategia de búsqueda de contexto:
            # 1. Si hay referencia -> Buscar por referencia
            # 2. Si NO hay referencia -> Buscar por similitud en descripción (ej. "Traslado A Fondo")
            
            if referencia_mov:
                cursor.execute("""
                    SELECT m.Fecha, m.Descripcion, m.Referencia, m.Valor,
                           t.tercero, g.grupo, c.concepto,
                           m.TerceroID, m.GrupoID, m.ConceptoID
                    FROM movimientos m
                    LEFT JOIN terceros t ON m.TerceroID = t.terceroid
                    LEFT JOIN grupos g ON m.GrupoID = g.grupoid
                    LEFT JOIN conceptos c ON m.ConceptoID = c.conceptoid
                    WHERE m.Referencia = %s
                      AND m.Fecha < %s
                      AND m.TerceroID IS NOT NULL
                    ORDER BY m.Fecha DESC
                    LIMIT 5
                """, (referencia_mov, fecha_mov))
                self.agregar_log(f"🔍 Buscando contexto con referencia: {referencia_mov}", 'info')
            else:
                palabras = desc_mov.split()
                prefijo = " ".join(palabras[:2]) if len(palabras) >= 2 else (palabras[0] if palabras else "")
                
                cursor.execute("""
                    SELECT m.Fecha, m.Descripcion, m.Referencia, m.Valor,
                           t.tercero, g.grupo, c.concepto,
                           m.TerceroID, m.GrupoID, m.ConceptoID
                    FROM movimientos m
                    LEFT JOIN terceros t ON m.TerceroID = t.terceroid
                    LEFT JOIN grupos g ON m.GrupoID = g.grupoid
                    LEFT JOIN conceptos c ON m.ConceptoID = c.conceptoid
                    WHERE m.Descripcion LIKE %s
                      AND m.Fecha < %s
                      AND m.TerceroID IS NOT NULL
                    ORDER BY m.Fecha DESC
                    LIMIT 5
                """, (f"%{prefijo}%", fecha_mov))
                self.agregar_log(f"🔍 Buscando contexto por descripción similar: {prefijo}...", 'info')
            
            self.contexto_historico = cursor.fetchall()
            
            # Limpiar TreeView de contexto
            for item in self.contexto_tree.get_children():
                self.contexto_tree.delete(item)
            
            # Poblar TreeView
            for idx, ctx in enumerate(self.contexto_historico):
                try:
                    c_fecha, c_desc, c_ref, c_valor, c_tercero, c_grupo, c_concepto, c_tid, c_gid, c_cid = ctx
                    self.contexto_tree.insert('', 'end', values=(
                        c_fecha.strftime('%Y-%m-%d'),
                        c_desc[:40],
                        c_ref if c_ref else '',
                        f"${c_valor:,.2f}",
                        f"{c_tid}-{c_tercero}" if c_tercero else '',
                        f"{c_gid}-{c_grupo}" if c_grupo else '',
                        f"{c_cid}-{c_concepto}" if c_concepto else ''
                    ))
                except Exception as ctx_err:
                    self.agregar_log(f"✗ ERROR procesando fila de contexto: {ctx_err}", 'error')
            
            self.agregar_log(f"✓ Cargados {len(self.contexto_historico)} registros de contexto relevante", 'success')
            
            # Limpiar selección previa
            self.tercero_combo.set('')
            self.tercero_seleccionado_id = None
                    
            tercero_asignado_por_regla = False
            
            # 1. Aplicar REGLA DE NEGOCIO (Prioridad Máxima)
            if self.regla_actual:
                tid = self.regla_actual['tid']
                cursor.execute("SELECT terceroid, tercero FROM terceros WHERE terceroid = %s", (tid,))
                res = cursor.fetchone()
                if res:
                    t_db, tname = res
                    self.tercero_combo.set(f"{t_db}: {tname}")
                    self.tercero_seleccionado_id = t_db
                    self.agregar_log(f"✨ Regla aplicada: '{self.regla_actual['patron']}' -> Tercero {t_db}", 'success')
                    tercero_asignado_por_regla = True
            
            if not tercero_asignado_por_regla:
                # 2. Intentar buscar por REFERENCIA exacta en TERCEROS (Maestro)
                tercero_encontrado_por_ref = None
                origen_ref = ""
                if referencia_mov:
                    # a) Buscar en tabla tercero_descripciones (referencia está ahí después de 3NF)
                    cursor.execute("""
                        SELECT t.terceroid, t.tercero 
                        FROM terceros t
                        JOIN tercero_descripciones td ON t.terceroid = td.terceroid
                        WHERE td.referencia = %s AND td.activa = TRUE
                        LIMIT 1
                    """, (referencia_mov,))
                    tercero_encontrado_por_ref = cursor.fetchone()
                    if tercero_encontrado_por_ref:
                        origen_ref = "Maestro"
                    else:
                        # b) Buscar en Histórico de Movimientos
                        cursor.execute("""
                            SELECT t.terceroid, t.tercero 
                            FROM movimientos m
                            JOIN terceros t ON m.TerceroID = t.terceroid
                            WHERE m.Referencia = %s AND m.TerceroID IS NOT NULL
                            LIMIT 1
                        """, (referencia_mov,))
                        tercero_encontrado_por_ref = cursor.fetchone()
                        if tercero_encontrado_por_ref:
                            origen_ref = "Historial"
                
                if tercero_encontrado_por_ref:
                     tid, tname = tercero_encontrado_por_ref
                     self.tercero_combo.set(f"{tid}: {tname}")
                     self.tercero_seleccionado_id = tid
                     self.agregar_log(f"✓ Tercero encontrado por Referencia ({origen_ref}): {referencia_mov}", 'success')
                     # Cargar lista completa
                     self.cargar_terceros_para_busqueda() 
                else:
                    tercero_encontrado_en_contexto = False
                    
                    # 3. Intentar buscar en el Contexto Histórico Recién Cargado (Prioridad sobre Fuzzy)
                    if self.contexto_historico:
                        # El contexto viene ordenado por fecha DESC, tomamos el primero que tenga Tercero
                        for ctx in self.contexto_historico:
                            # ctx indices: ... fecha(0), desc(1), ref(2), val(3), tercero_str(4) ... tid(7)
                            ctx_tid = ctx[7]
                            ctx_tname = ctx[4] # Este string puede venir como "ID-Nombre" o solo Nombre? SQL dice: t.tercero
                            
                            if ctx_tid:
                                # Recuperar info completa del tercero para el combo
                                cursor.execute("SELECT tercero FROM terceros WHERE terceroid = %s", (ctx_tid,))
                                t_info = cursor.fetchone()
                                if t_info:
                                    tname = t_info[0]
                                    self.tercero_combo.set(f"{ctx_tid}: {tname}")
                                    self.tercero_seleccionado_id = ctx_tid
                                    self.agregar_log(f"✓ Tercero sugerido por historial reciente: {tname}", 'success')
                                    tercero_encontrado_en_contexto = True
                                    break
                    
                    if not tercero_encontrado_en_contexto:
                        # 4. Si no hay match por referencia ni historial, comportamiento normal
                        if referencia_mov:
                             self.agregar_log(f"ℹ Referencia '{referencia_mov}' no existe en Terceros ni historial. Abriendo creación...", 'warning')
                             # Abrir diálogo para crear nuevo tercero automáticamente
                             self.root.after(100, self.crear_nuevo_tercero)
                        
                        self.agregar_log(f"🔍 Buscando terceros similares para: '{desc_mov}'", 'info')
                        self.cargar_terceros_para_busqueda(desc_mov)
                    else:
                        # Si encontramos en contexto, igual cargamos la lista completa para permitir cambiar
                        self.cargar_terceros_para_busqueda()
            
            # Cargar y analizar grupos y conceptos
            self.cargar_grupos_conceptos(grupo_id, concepto_id)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.agregar_log(f"✗ Error al cargar contexto: {e}", 'error')

    def cargar_grupos_conceptos(self, grupo_id_actual, concepto_id_actual):
        """Carga los grupos y conceptos, sugiere basado en contexto."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Cargar todos los grupos
            cursor.execute("SELECT grupoid, grupo FROM grupos ORDER BY grupo")
            grupos = cursor.fetchall()
            
            # Guardar listas completas para filtrado
            self.grupos_completos = grupos
            self.grupo_combo['values'] = [f"{gid}: {nombre}" for gid, nombre in grupos]
            
            # Cargar todos los conceptos (sin filtro por ahora)
            cursor.execute("SELECT conceptoid, concepto, grupoid_fk FROM conceptos ORDER BY concepto")
            conceptos = cursor.fetchall()
            
            # Guardar lista completa de conceptos con grupoid_fk
            self.conceptos_completos = conceptos  # Ahora incluye grupoid_fk
            
            # Inicialmente mostrar todos los conceptos
            self.concepto_combo['values'] = [f"{cid}: {nombre}" for cid, nombre, gid in conceptos]
            
            # REGLA DE NEGOCIO: Grupo y Concepto
            regla_aplicada = False
            
            if self.regla_actual:
                 target_gid = self.regla_actual['gid']
                 target_cid = self.regla_actual['cid']
                 patron = self.regla_actual['patron']
                 
                 # Grupo
                 for gid, nombre in self.grupos_completos:
                      if gid == target_gid:
                           self.lbl_grupo_sugerido.config(text=f"✨ Regla ({patron}): {nombre}")
                           self.grupo_combo.set(f"{gid}: {nombre}")
                           self.grupo_seleccionado_id = gid
                           self.filtrar_conceptos_por_grupo()
                           break
                 
                 # Concepto
                 for cid, nombre, gid in self.conceptos_completos:
                      if cid == target_cid:
                           self.lbl_concepto_sugerido.config(text=f"✨ Regla ({patron}): {nombre}")
                           self.concepto_combo.set(f"{cid}: {nombre}")
                           self.concepto_seleccionado_id = cid
                           break
                 
                 regla_aplicada = True

            # Analizar contexto para sugerencias (solo si no aplicó regla)
            if not regla_aplicada and self.contexto_historico:
                # Extraer grupos y conceptos del contexto
                # c_fecha, c_desc, c_ref, c_valor, c_tercero, c_grupo, c_concepto, c_tid, c_gid, c_cid = ctx
                # indices: 0        1       2       3        4          5        6           7      8      9
                grupos_ctx = [ctx[8] for ctx in self.contexto_historico if ctx[8]]  # GrupoID
                conceptos_ctx = [ctx[9] for ctx in self.contexto_historico if ctx[9]]  # ConceptoID
                
                # Si todos los registros del contexto tienen el mismo grupo
                if grupos_ctx and len(set(grupos_ctx)) == 1:
                    grupo_sugerido_id = grupos_ctx[0]
                    cursor.execute("SELECT grupo FROM grupos WHERE grupoid = %s", (grupo_sugerido_id,))
                    grupo_nombre = cursor.fetchone()
                    if grupo_nombre:
                        self.lbl_grupo_sugerido.config(text=f"✓ Sugerido: {grupo_nombre[0]} (basado en contexto)")
                        # Preseleccionar en combo
                        for idx, val in enumerate(self.grupo_combo['values']):
                            if val.startswith(f"{grupo_sugerido_id}:"):
                                self.grupo_combo.current(idx)
                                self.grupo_seleccionado_id = grupo_sugerido_id
                                # Filtrar conceptos por este grupo
                                self.filtrar_conceptos_por_grupo()
                                break
                
                # Si todos los registros del contexto tienen el mismo concepto
                if conceptos_ctx and len(set(conceptos_ctx)) == 1:
                    concepto_sugerido_id = conceptos_ctx[0]
                    cursor.execute("SELECT concepto FROM conceptos WHERE conceptoid = %s", (concepto_sugerido_id,))
                    concepto_nombre = cursor.fetchone()
                    if concepto_nombre:
                        self.lbl_concepto_sugerido.config(text=f"✓ Sugerido: {concepto_nombre[0]} (basado en contexto)")
                        # Preseleccionar en combo
                        for idx, val in enumerate(self.concepto_combo['values']):
                            if val.startswith(f"{concepto_sugerido_id}:"):
                                self.concepto_combo.current(idx)
                                self.concepto_seleccionado_id = concepto_sugerido_id
                                break
            
            # Validar si se puede actualizar
            # Verificar si aplica para LOTE (Si hay regla activa)
            if self.regla_actual:
                self.verificar_lote_automatico()
            
            # Formatear listas para combos "ID: Nombre"
            self.lista_grupos_formato = [f"{gid}: {nombre}" for gid, nombre in grupos]
            
            self.setup_filtering(self.grupo_combo, self.lista_grupos_formato)
            
            # Validar si se puede actualizar
            self.validar_actualizacion()
            # Haremos que setup_filtering acepte una lambda que devuelva self.concepto_combo['values'] original?
            # Lo mejor es que filtrar filtrará sobre 'conceptos_completos' pero respetando grupo.
            
            # Implementación custom para conceptos
            def get_conceptos_validos():
                if self.grupo_seleccionado_id:
                     return [f"{cid}: {nombre}" for cid, nombre, gid in self.conceptos_completos if gid == self.grupo_seleccionado_id]
                else:
                     return [f"{cid}: {nombre}" for cid, nombre, gid in self.conceptos_completos]

            self.setup_filtering(self.concepto_combo, get_conceptos_validos)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.agregar_log(f"✗ Error al cargar grupos/conceptos: {e}", 'error')
    
    def filtrar_grupos(self, event):
        """Filtra grupos mientras el usuario escribe."""
        texto_busqueda = self.grupo_combo.get().lower()
        
        if not hasattr(self, 'grupos_completos'):
            return
        
        if texto_busqueda:
            grupos_filtrados = [(gid, nombre) for gid, nombre in self.grupos_completos 
                               if texto_busqueda in nombre.lower() or texto_busqueda in str(gid)]
        else:
            grupos_filtrados = self.grupos_completos
        
        self.grupo_combo['values'] = [f"{gid}: {nombre}" for gid, nombre in grupos_filtrados]
    
    def filtrar_conceptos(self, event):
        """Filtra conceptos mientras el usuario escribe."""
        texto_busqueda = self.concepto_combo.get().lower()
        
        if not hasattr(self, 'conceptos_completos'):
            return
        
        # Filtrar por grupo si hay uno seleccionado
        if self.grupo_seleccionado_id:
            conceptos_base = [(cid, nombre) for cid, nombre, gid in self.conceptos_completos 
                             if gid == self.grupo_seleccionado_id]
        else:
            conceptos_base = [(cid, nombre) for cid, nombre, gid in self.conceptos_completos]
        
        # Filtrar por texto
        if texto_busqueda:
            conceptos_filtrados = [(cid, nombre) for cid, nombre in conceptos_base 
                                  if texto_busqueda in nombre.lower() or texto_busqueda in str(cid)]
        else:
            conceptos_filtrados = conceptos_base
        
        self.concepto_combo['values'] = [f"{cid}: {nombre}" for cid, nombre in conceptos_filtrados]
    
    def filtrar_conceptos_por_grupo(self):
        """Filtra los conceptos basándose en el grupo seleccionado."""
        if not hasattr(self, 'conceptos_completos'):
            return
        
        if self.grupo_seleccionado_id:
            conceptos_filtrados = [(cid, nombre) for cid, nombre, gid in self.conceptos_completos 
                                  if gid == self.grupo_seleccionado_id]
            self.concepto_combo['values'] = [f"{cid}: {nombre}" for cid, nombre in conceptos_filtrados]
            self.concepto_combo.set('')  # Limpiar selección
            self.concepto_seleccionado_id = None
            self.lbl_concepto_sugerido.config(text="")
        else:
            # Mostrar todos
            self.concepto_combo['values'] = [f"{cid}: {nombre}" for cid, nombre, gid in self.conceptos_completos]
    
    def on_tercero_enter(self, event):
        """Maneja la selección de tercero por ID al presionar Enter."""
        texto = self.tercero_combo.get().strip()
        if not texto.isdigit():
            return
        
        tid_buscado = int(texto)
        if not hasattr(self, 'terceros_completos'):
            return
            
        # Buscar en la lista completa
        encontrado = None
        for item in self.terceros_completos:
            # item puede ser (id, tercero, desc, ref) o (id, tercero, desc, ref, score)
            if item[0] == tid_buscado:
                encontrado = item
                break
        
        if encontrado:
            tid, tname = encontrado[0], encontrado[1]
            texto_final = f"{tid}: {tname}"
            self.tercero_combo.set(texto_final)
            self.tercero_seleccionado_id = tid
            self.tercero_combo.icursor(tk.END)
            self.agregar_log(f"⚡ Selección rápida por ID: Tercero {tid}", 'info')
            self.validar_actualizacion()
        else:
            self.agregar_log(f"⚠ No se encontró Tercero con ID={tid_buscado}", 'warning')

    def on_grupo_enter(self, event):
        """Maneja la selección de grupo por ID al presionar Enter."""
        texto = self.grupo_combo.get().strip()
        if not texto.isdigit():
            return
        
        gid_buscado = int(texto)
        if not hasattr(self, 'grupos_completos'):
            return
            
        encontrado = None
        for gid, nombre in self.grupos_completos:
            if gid == gid_buscado:
                encontrado = (gid, nombre)
                break
                
        if encontrado:
            gid, nombre = encontrado
            self.grupo_combo.set(f"{gid}: {nombre}")
            self.grupo_seleccionado_id = gid
            self.grupo_combo.icursor(tk.END)
            self.agregar_log(f"⚡ Selección rápida por ID: Grupo {gid}", 'info')
            self.filtrar_conceptos_por_grupo()
            self.validar_actualizacion()
            self.concepto_combo.focus_set() # Pasar al siguiente campo
        else:
            self.agregar_log(f"⚠ No se encontró Grupo con ID={gid_buscado}", 'warning')

    def on_concepto_enter(self, event):
        """Maneja la selección de concepto por ID al presionar Enter."""
        texto = self.concepto_combo.get().strip()
        if not texto.isdigit():
            return
        
        cid_buscado = int(texto)
        if not hasattr(self, 'conceptos_completos'):
            return
            
        encontrado = None
        for cid, nombre, gid in self.conceptos_completos:
            if cid == cid_buscado:
                encontrado = (cid, nombre)
                break
                
        if encontrado:
            cid, nombre = encontrado
            self.concepto_combo.set(f"{cid}: {nombre}")
            self.concepto_seleccionado_id = cid
            self.concepto_combo.icursor(tk.END)
            self.agregar_log(f"⚡ Selección rápida por ID: Concepto {cid}", 'info')
            self.validar_actualizacion()
            # Si ya se puede actualizar, poner foco en botón
            if self.update_button['state'] == 'normal':
                self.update_button.focus_set()
        else:
            self.agregar_log(f"⚠ No se encontró Concepto con ID={cid_buscado}", 'warning')

    def on_grupo_seleccionado(self, event):
        """Maneja la selección de un grupo."""
        seleccion = self.grupo_combo.get()
        if seleccion and ':' in seleccion:
            # Extraer ID del formato "ID: Nombre"
            self.grupo_seleccionado_id = int(seleccion.split(':')[0])
            self.agregar_log(f"Grupo seleccionado: ID={self.grupo_seleccionado_id}", 'info')
            # Filtrar conceptos por este grupo
            self.filtrar_conceptos_por_grupo()
            self.validar_actualizacion()
    
    def on_concepto_seleccionado(self, event):
        """Maneja la selección de un concepto."""
        seleccion = self.concepto_combo.get()
        if seleccion and ':' in seleccion:
            # Extraer ID del formato "ID: Nombre"
            self.concepto_seleccionado_id = int(seleccion.split(':')[0])
            self.agregar_log(f"Concepto seleccionado: ID={self.concepto_seleccionado_id}", 'info')
            self.validar_actualizacion()
    
    def validar_actualizacion(self):
        """Valida si se puede habilitar el botón actualizar."""
        if not self.movimiento_actual:
            self.update_button.config(state='disabled')
            return
        
        mov_id, fecha, desc, ref, valor, tercero_id, grupo_id, concepto_id, detalle = self.movimiento_actual
        
        # Determinar qué falta
        falta_tercero = tercero_id is None
        falta_grupo = grupo_id is None
        falta_concepto = concepto_id is None
        
        # Para poder actualizar:
        # - Si falta grupo, debe estar seleccionado
        # - Si falta concepto, debe estar seleccionado
        # - Tercero ya está OK (o también debe seleccionarse en el futuro)
        
        puede_actualizar = True
        
        if self.tercero_seleccionado_id is None:
            puede_actualizar = False
        
        if self.grupo_seleccionado_id is None:
            puede_actualizar = False
        
        if self.concepto_seleccionado_id is None:
            puede_actualizar = False
        
        if puede_actualizar:
            self.update_button.config(state='normal')
        else:
            # Plan B: Check simple text presence as requested
            t_val = self.tercero_combo.get().strip()
            g_val = self.grupo_combo.get().strip()
            c_val = self.concepto_combo.get().strip()
            
            if t_val and g_val and c_val:
                 self.update_button.config(state='normal')
            else:
                 self.update_button.config(state='disabled')
    
    # Funciones legacy eliminadas (actualizar_registro y limpiar_editor antiguos)

    
    def saltar_movimiento(self):
        """Salta al siguiente movimiento pendiente."""
        self.limpiar_editor()
        self.agregar_log("⏭ Editor limpiado - selecciona otro movimiento", 'info')

    def cargar_terceros_para_busqueda(self, descripcion_mov=None):
        """Carga la lista de terceros, con fuzzy matching si hay descripción.
        Después de 3NF, descripcion/referencia están en tercero_descripciones.
        """
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Cargar solo terceros (sin descripcion/referencia - esas están en tercero_descripciones)
            cursor.execute("""
                SELECT terceroid, tercero
                FROM terceros
                WHERE activa = TRUE
                ORDER BY tercero
            """)
            
            terceros = cursor.fetchall()
            self.terceros_completos = terceros
            
            # Si hay descripción del movimiento, buscar coincidencias en tercero_descripciones
            if descripcion_mov:
                desc_mov_lower = descripcion_mov.lower()
                
                # Buscar coincidencias en tercero_descripciones
                cursor.execute("""
                    SELECT DISTINCT t.terceroid, t.tercero, td.descripcion
                    FROM terceros t
                    JOIN tercero_descripciones td ON t.terceroid = td.terceroid
                    WHERE td.activa = TRUE AND t.activa = TRUE
                      AND LOWER(td.descripcion) = %s
                """, (desc_mov_lower,))
                exactos = cursor.fetchall()
                
                if exactos:
                    # Encontramos coincidencia exacta por descripción en alias
                    self.tercero_combo['values'] = [f"{t[0]}: {t[1]}" for t in exactos]
                    self.agregar_log(f"✓ Encontrado tercero exacto por alias: {exactos[0][1]}", 'success')
                    if len(exactos) == 1:
                        self.tercero_combo.set(self.tercero_combo['values'][0])
                        self.tercero_seleccionado_id = exactos[0][0]
                        self.validar_actualizacion()
                    cursor.close()
                    conn.close()
                    return
                
                # Si no hay exactos, buscar por nombre del tercero
                cursor.execute("""
                    SELECT terceroid, tercero
                    FROM terceros
                    WHERE activa = TRUE AND LOWER(tercero) = %s
                """, (desc_mov_lower,))
                por_nombre = cursor.fetchall()
                
                if por_nombre:
                    self.tercero_combo['values'] = [f"{t[0]}: {t[1]}" for t in por_nombre]
                    self.agregar_log(f"✓ Encontrado tercero exacto por nombre: {por_nombre[0][1]}", 'success')
                    if len(por_nombre) == 1:
                        self.tercero_combo.set(self.tercero_combo['values'][0])
                        self.tercero_seleccionado_id = por_nombre[0][0]
                        self.validar_actualizacion()
                    cursor.close()
                    conn.close()
                    return
                
                # Si no hay exactos, usar fuzzy matching en tercero_descripciones
                cursor.execute("""
                    SELECT DISTINCT t.terceroid, t.tercero, td.descripcion
                    FROM terceros t
                    JOIN tercero_descripciones td ON t.terceroid = td.terceroid
                    WHERE td.activa = TRUE AND t.activa = TRUE
                """)
                terceros_con_alias = cursor.fetchall()
                
                terceros_con_score = []
                for tid, tercero, desc in terceros_con_alias:
                    if desc:
                        score = fuzz.token_set_ratio(descripcion_mov.lower(), desc.lower())
                        terceros_con_score.append((tid, tercero, score))
                    else:
                        terceros_con_score.append((tid, tercero, 0))
                
                # Ordenar por score descendente
                terceros_con_score.sort(key=lambda x: x[2], reverse=True)
                
                # Filtrar solo los que tienen más de 60% de similitud
                UMBRAL_SIMILITUD = 60
                terceros_similares = [(tid, t, s) for tid, t, s in terceros_con_score if s >= UMBRAL_SIMILITUD]
                
                if terceros_similares:
                    self.tercero_combo['values'] = [
                        f"{tid}: {tercero}" 
                        for tid, tercero, score in terceros_similares
                    ]
                    self.agregar_log(f"✓ Encontrados {len(terceros_similares)} terceros similares a '{descripcion_mov[:30]}...'", 'success')
                else:
                    # No hay similares, mostrar todos
                    self.tercero_combo['values'] = [
                        f"{tid}: {tercero}" 
                        for tid, tercero in terceros
                    ]
                    self.agregar_log(f"⚠ No hay terceros similares. Mostrando todos ({len(terceros)})", 'warning')
            else:
                # Sin descripción, mostrar todos (Solo ID - Nombre)
                self.tercero_combo['values'] = [
                    f"{tid}: {tercero}" 
                    for tid, tercero in terceros
                ]
                self.agregar_log(f"✓ Cargados {len(terceros)} terceros", 'info')
                
            self.setup_filtering(self.tercero_combo, self.tercero_combo['values'])
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.agregar_log(f"✗ Error al cargar terceros: {e}", 'error')
    
    def filtrar_terceros(self, event):
        """Filtra terceros mientras el usuario escribe."""
        texto_busqueda = self.tercero_combo.get().lower()
        
        if not hasattr(self, 'terceros_completos'):
            return
        
        if texto_busqueda:
            terceros_filtrados = [
                (tid, tercero) for tid, tercero in self.terceros_completos 
                if texto_busqueda in tercero.lower() or 
                   texto_busqueda in str(tid)
            ]
        else:
            terceros_filtrados = self.terceros_completos
        
        self.tercero_combo['values'] = [
            f"{tid}: {tercero}" 
            for tid, tercero in terceros_filtrados
        ]
    
    def on_tercero_seleccionado(self, event):
        """Maneja la selección de un tercero."""
        seleccion = self.tercero_combo.get()
        if seleccion and ':' in seleccion:
            # Extraer ID del formato "ID: Nombre - Descripcion"
            self.tercero_seleccionado_id = int(seleccion.split(':')[0])
            self.agregar_log(f"Tercero seleccionado: ID={self.tercero_seleccionado_id}", 'info')
            self.validar_actualizacion()
    
    def mostrar_busqueda_tercero(self):
        """Muestra el combo de búsqueda de tercero."""
        self.lbl_tercero_actual.grid_forget()
        self.btn_cambiar_tercero.grid_forget()
        self.tercero_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.btn_crear_tercero.grid(row=0, column=1, padx=2)
        self.cargar_terceros_para_busqueda()
    
    def crear_nuevo_tercero(self):
        """Abre diálogo para crear un nuevo tercero."""
        if not self.movimiento_actual:
            return
        
        mov_id, fecha, desc, ref, valor, tercero_id, grupo_id, concepto_id, detalle = self.movimiento_actual
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title("Crear Nuevo Tercero")
        
        # Dimensiones
        width = 500
        height = 250
        
        # Centrar respecto a la ventana principal
        try:
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            root_w = self.root.winfo_width()
            root_h = self.root.winfo_height()
            
            x = root_x + (root_w // 2) - (width // 2)
            y = root_y + (root_h // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
        except:
            dialog.geometry(f"{width}x{height}")

        dialog.transient(self.root)
        dialog.grab_set()
        dialog.lift()
        
        # Campos
        ttk.Label(dialog, text="Tercero (requerido):", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        entry_tercero = ttk.Entry(dialog, width=40)
        entry_tercero.grid(row=0, column=1, padx=10, pady=5)
        
        # Mensaje de ayuda (3NF: descripcion/referencia ahora están en tercero_descripciones)
        ttk.Label(dialog, text="Nota: Las descripciones/alias se gestionan en 'Alias Terceros'.", 
                 font=('Arial', 8, 'italic'), foreground='gray').grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        
        def guardar_tercero():
            tercero_nombre = entry_tercero.get().strip()
            
            if not tercero_nombre:
                messagebox.showerror("Error", "El campo 'Tercero' es requerido")
                return
            
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                # Validar existencia previa (solo por nombre ahora)
                cursor.execute("""
                    SELECT terceroid FROM terceros 
                    WHERE lower(tercero) = %s
                """, (tercero_nombre.lower(),))
                
                existe = cursor.fetchone()
                if existe:
                    messagebox.showerror("Duplicado", f"Ya existe un tercero con ese nombre (ID: {existe[0]}).\nNombre: {tercero_nombre}")
                    cursor.close()
                    conn.close()
                    return

                # Insertar nuevo tercero (solo columnas existentes: tercero, activa)
                cursor.execute("""
                    INSERT INTO terceros (tercero)
                    VALUES (%s)
                    RETURNING terceroid
                """, (tercero_nombre,))
                
                nuevo_id = cursor.fetchone()[0]
                conn.commit()
                
                self.agregar_log(f"✓ Tercero creado: ID={nuevo_id}, {tercero_nombre}", 'success')
                
                cursor.close()
                conn.close()
                
                # Seleccionar el nuevo tercero
                self.tercero_seleccionado_id = nuevo_id
                self.tercero_combo.set(f"{nuevo_id}: {tercero_nombre}")
                
                # Recargar lista
                self.cargar_terceros_para_busqueda()
                
                # Validar actualización
                self.validar_actualizacion()
                
                dialog.destroy()
                messagebox.showinfo("Éxito", f"Tercero '{tercero_nombre}' creado correctamente")
                
            except psycopg2.IntegrityError as e:
                conn.rollback()
                self.agregar_log(f"✗ Error: Tercero duplicado - {e}", 'error')
                messagebox.showerror("Error", f"Ya existe un tercero con ese nombre:\n{e}")
            except Exception as e:
                conn.rollback()
                self.agregar_log(f"✗ Error al crear tercero: {e}", 'error')
                messagebox.showerror("Error", f"Error al crear tercero:\n{e}")
        
        # Botones
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Guardar", command=guardar_tercero, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy, width=15).grid(row=0, column=1, padx=5)

    def detectar_regla(self, descripcion):
        """Busca si la descripción coincide con alguna regla predefinida."""
        if not descripcion:
            return None
        
        desc_lower = descripcion.lower()
        for regla in self.REGLAS:
            if regla['patron'].lower() in desc_lower:
                return regla
        return None

    def verificar_lote_automatico(self):
        """Verifica si hay más movimientos que cumplen la regla actual."""
        try:
            if not self.movimiento_actual or not self.regla_actual:
                return

            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Usamos parámetro para el patrón
            patron = f"%{self.regla_actual['patron']}%"
            current_id = self.movimiento_actual[0]
            
            cursor.execute("""
                SELECT COUNT(*)
                FROM movimientos
                WHERE Descripcion ILIKE %s
                  AND Id != %s
                  AND (TerceroID IS NULL OR GrupoID IS NULL OR ConceptoID IS NULL)
            """, (patron, current_id))
            
            row = cursor.fetchone()
            count = row[0] if row else 0
            
            if count > 0:
                self.btn_batch_update.config(text=f"⚡ Aplicar a Todos ({count} más)", state='normal')
                self.agregar_log(f"ℹ Se detectaron {count} movimientos adicionales ('{self.regla_actual['patron']}') para procesar en lote.", 'info')
            else:
                self.btn_batch_update.config(text="⚡ Aplicar a Todos", state='disabled')
            
            cursor.close()
            conn.close()
        except Exception as e:
            self.agregar_log(f"✗ Error verificando lote: {e}", 'error')
            print(f"Error detallado lote: {e}")

    def actualizar_lote(self):
        """Aplica la regla automática a todos los movimientos pendientes similares."""
        if not self.movimiento_actual or not self.regla_actual:
            return

        tid = self.regla_actual['tid']
        gid = self.regla_actual['gid']
        cid = self.regla_actual['cid']
        patron_texto = self.regla_actual['patron']

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Usar parámetros para todo para evitar conflictos con %
            patron_sql = f"%{patron_texto}%"
            current_id = self.movimiento_actual[0]
            
            # 1. Calcular estadísticas para confirmación
            cursor.execute("""
                SELECT COUNT(*), SUM(Valor)
                FROM movimientos
                WHERE Descripcion ILIKE %s
                  AND (
                      (TerceroID IS NULL OR GrupoID IS NULL OR ConceptoID IS NULL)
                      OR Id = %s
                  )
            """, (patron_sql, current_id))
            
            res = cursor.fetchone()
            count = res[0] if res else 0
            total_valor = res[1] if res and res[1] else 0
            
            msg = (f"¿Está seguro de clasificar TODOS los movimientos de '{patron_texto}'?\n\n"
                   f"📊 Cantidad de Registros: {count}\n"
                   f"💰 Valor Total: ${total_valor:,.2f}\n\n"
                   f"Se asignará automáticamente:\n"
                   f"• Tercero: {tid}\n"
                   f"• Grupo: {gid}\n"
                   f"• Concepto: {cid}")
            
            if not messagebox.askyesno("Confirmar Lote", msg):
                cursor.close()
                conn.close()
                return

            # 2. Ejecutar actualización
            cursor.execute("""
                UPDATE movimientos
                SET TerceroID = %s, GrupoID = %s, ConceptoID = %s
                WHERE Descripcion ILIKE %s
                  AND (
                      (TerceroID IS NULL OR GrupoID IS NULL OR ConceptoID IS NULL)
                      OR Id = %s
                  )
            """, (tid, gid, cid, patron_sql, current_id))
            
            filas_afectadas = cursor.rowcount
            conn.commit()
            
            self.agregar_log(f"🚀 Lote procesado: {filas_afectadas} movimientos actualizados.", 'success')
            messagebox.showinfo("Lote Procesado", f"Se actualizaron {filas_afectadas} movimientos correctamente.")
            
            cursor.close()
            conn.close()
            
            # Recargar todo
            self.cargar_movimientos_pendientes()
            self.limpiar_editor()
            
        except Exception as e:
            self.agregar_log(f"✗ Error al procesar lote: {e}", 'error')
            messagebox.showerror("Error", f"Error en lote: {e}")

    def seleccionar_por_id(self, combo):
        """Busca el ID ingresado en los valores del combo y lo selecciona."""
        texto = combo.get().strip()
        # Permitir formato "ID:" sin ser puramente digito si el usuario lo escribe asi, 
        # pero principalmente chequeamos si empieza con un número
        if not texto or not texto[0].isdigit():
            return
            
        # Extraer solo la parte numérica inicial
        search_id_str = ""
        for char in texto:
            if char.isdigit():
                search_id_str += char
            else:
                break
        
        if not search_id_str: 
            return

        prefix = f"{search_id_str}:" # En este archivo el formato es "ID: Nombre" (con dos puntos)
        
        # Buscar en los valores actuales del combo
        for value in combo['values']:
            if value.startswith(prefix):
                combo.set(value)
                combo.icursor(tk.END)
                
                # Disparar eventos de selección si es necesario
                if combo == self.grupo_combo:
                    self.on_grupo_seleccionado(None)
                elif combo == self.concepto_combo:
                    self.on_concepto_seleccionado(None)
                elif combo == self.tercero_combo:
                    self.on_tercero_seleccionado(None)
                    
                return
        
        # Si no lo encuentra, intentar buscar el ID exacto aunque tenga otro formato
        # A veces el usuario escribe "205" y en la lista sale "205: Varios"
        
        messagebox.showwarning("No encontrado", f"No se encontró el ID {search_id_str} en la lista actual.")

    def setup_filtering(self, combo, source_list_ref):
        """
        Configura el filtrado 'mientras escribes' para un combobox.
        """
        def on_key(event):
            if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape'):
                return
            
            # Obtener lista completa actual
            full_list = source_list_ref() if callable(source_list_ref) else source_list_ref
            
            typed = combo.get().lower()
            if not typed:
                combo['values'] = full_list
            else:
                filtered = [item for item in full_list if typed in item.lower()]
                combo['values'] = filtered
                
        combo.bind('<KeyRelease>', on_key)

def main():
    """Función principal."""
    root = tk.Tk()
    app = AsignarClasificacionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
