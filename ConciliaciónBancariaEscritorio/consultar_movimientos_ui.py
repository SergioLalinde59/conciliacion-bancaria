#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consulta y Edición de Movimientos
Permite filtrar movimientos por fecha y texto, visualizar todos los detalles
y editar la clasificación (Tercero, Grupo, Concepto) y datos del registro.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from tkcalendar import DateEntry  # Requiere: pip install tkcalendar

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

class ConsultarMovimientosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Consulta de Movimientos - Gastos SLB")
        self.root.geometry("1400x800")
        
        # Variables de datos
        self.movimientos = []
        self.terceros_lista = []
        self.grupos_lista = []
        self.conceptos_lista = []
        self.cuentas_lista = []
        self.monedas_lista = []
        
        # Listas filtradas para UI
        self.conceptos_f_validos = [] 
        
        # Filtro signo: 'todos', 'pos', 'neg'
        self.filtro_signo = 'todos'
        
        # Configuración de estilos
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=25)
        
        self.setup_ui()
        self.cargar_catalogos()
        self.buscar_movimientos()  # Carga inicial

    def _centrar_caja_dialogo(self, ventana, ancho_min=350, alto_min=180):
        """Centra una ventana emergente sobre la aplicación principal."""
        ventana.update_idletasks()
        w = ventana.winfo_reqwidth()
        h = ventana.winfo_reqheight()
        
        # Asegurar mínimos
        w = max(w, ancho_min)
        h = max(h, alto_min)
        
        # Obtener geometría app
        self.root.update_idletasks()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        
        x = root_x + (root_w - w) // 2
        y = root_y + (root_h - h) // 2
        
        ventana.geometry(f"{w}x{h}+{x}+{y}")

    def mostrar_mensaje(self, titulo, mensaje, tipo='info'):
        """Muestra mensaje centrado reemplazando messagebox."""
        dlg = tk.Toplevel(self.root)
        dlg.title(titulo)
        dlg.transient(self.root)
        dlg.grab_set()
        
        # Colores e iconos
        colors = {'info': '#0055aa', 'warning': '#ffaa00', 'error': '#cc0000', 'success': '#008800'}
        icons = {'info': 'ℹ', 'warning': '⚠', 'error': '❌', 'success': '✓'}
        
        color = colors.get(tipo, 'black')
        icon = icons.get(tipo, 'ℹ')
        
        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=icon, font=('Arial', 24), foreground=color).pack(pady=(0, 10))
        ttk.Label(frame, text=mensaje, wraplength=380, justify=tk.CENTER, font=('Arial', 10)).pack(pady=(0, 20))
        
        ttk.Button(frame, text="Aceptar", command=dlg.destroy).pack()
        
        self._centrar_caja_dialogo(dlg)
        self.root.wait_window(dlg)

    def setup_ui(self):
        # --- Frame Principal ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- 1. Panel de Filtros ---
        filter_frame = ttk.LabelFrame(main_frame, text="Filtros de Búsqueda", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # Contenedor para filtros (Izquierda)
        filters_container = ttk.Frame(filter_frame)
        filters_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Contenedor para botones (Derecha)
        buttons_container = ttk.Frame(filter_frame)
        buttons_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Contenedor filtros - Fila 0 (Botones Rápidos Fecha)
        row0 = ttk.Frame(filters_container)
        row0.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row0, text="Rangos Rápidos:").pack(side=tk.LEFT)
        
        ttk.Button(row0, text="Mes Actual", command=lambda: self.set_date_range('this_month'), width=10)\
            .pack(side=tk.LEFT, padx=2)
        ttk.Button(row0, text="Mes Ant.", command=lambda: self.set_date_range('last_month'), width=10)\
            .pack(side=tk.LEFT, padx=2)
        ttk.Button(row0, text="Últ. 3 Meses", command=lambda: self.set_date_range('last_3m'), width=12)\
            .pack(side=tk.LEFT, padx=2)
        ttk.Button(row0, text="Año (YTD)", command=lambda: self.set_date_range('ytd'), width=10)\
            .pack(side=tk.LEFT, padx=2)
        ttk.Button(row0, text="Últ. 12 Meses", command=lambda: self.set_date_range('last_12m'), width=12)\
            .pack(side=tk.LEFT, padx=2)

        ttk.Label(row0, text="|  Tipo:").pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(row0, text="Todos", command=lambda: self.set_signo('todos'), width=8)\
            .pack(side=tk.LEFT, padx=1)
        ttk.Button(row0, text="Ingresos (+)", command=lambda: self.set_signo('pos'), width=10)\
            .pack(side=tk.LEFT, padx=1)
        ttk.Button(row0, text="Gastos (-)", command=lambda: self.set_signo('neg'), width=10)\
            .pack(side=tk.LEFT, padx=1)

        # --- Fila 1: Fechas y Buscador Texto ---
        row1 = ttk.Frame(filters_container)
        row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(row1, text="Desde:").pack(side=tk.LEFT)
        self.date_from = DateEntry(row1, width=12, background='darkblue',
                                 foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        # Por defecto primer día del mes actual
        today = date.today()
        first_day = today.replace(day=1)
        self.date_from.set_date(first_day)
        self.date_from.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Hasta:").pack(side=tk.LEFT)
        self.date_to = DateEntry(row1, width=12, background='darkblue',
                               foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_to.set_date(today)
        self.date_to.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Buscar (Desc/Ref/Tercero/Valor):").pack(side=tk.LEFT, padx=(15, 5))
        self.txt_search = ttk.Entry(row1)
        self.txt_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.txt_search.bind('<Return>', lambda e: self.buscar_movimientos())

        # --- Fila 2: Clasificación ---
        row2 = ttk.Frame(filters_container)
        row2.pack(fill=tk.X)

        ttk.Label(row2, text="Cuenta:").pack(side=tk.LEFT)
        self.cb_filter_cuenta = ttk.Combobox(row2, width=20)
        self.cb_filter_cuenta.pack(side=tk.LEFT, padx=5)
        self.cb_filter_cuenta.bind('<Return>', lambda e: self.seleccionar_por_id(self.cb_filter_cuenta))

        ttk.Label(row2, text="Tercero:").pack(side=tk.LEFT, padx=(10, 0))
        self.cb_filter_tercero = ttk.Combobox(row2, width=30)
        self.cb_filter_tercero.pack(side=tk.LEFT, padx=5)
        self.cb_filter_tercero.bind('<Return>', lambda e: self.seleccionar_por_id(self.cb_filter_tercero))

        ttk.Label(row2, text="Grupo:").pack(side=tk.LEFT, padx=(10, 0))
        self.cb_filter_grupo = ttk.Combobox(row2, width=20)
        self.cb_filter_grupo.pack(side=tk.LEFT, padx=5)
        
        # Función wrapper para filtrar al dar Enter
        def on_grupo_enter(e):
            self.seleccionar_por_id(self.cb_filter_grupo)
            self.filtrar_conceptos_panel()
            
        self.cb_filter_grupo.bind('<Return>', on_grupo_enter)
        self.cb_filter_grupo.bind('<<ComboboxSelected>>', self.filtrar_conceptos_panel)

        ttk.Label(row2, text="Concepto:").pack(side=tk.LEFT, padx=(10, 0))
        self.cb_filter_concepto = ttk.Combobox(row2, width=20)
        self.cb_filter_concepto.pack(side=tk.LEFT, padx=5)
        self.cb_filter_concepto.bind('<Return>', lambda e: self.seleccionar_por_id(self.cb_filter_concepto))

        # --- Botones (Extremo Derecho) ---
        ttk.Button(buttons_container, text="🔍 Buscar", command=self.buscar_movimientos, width=12)\
            .pack(side=tk.TOP, pady=2)
        ttk.Button(buttons_container, text="🧹 Limpiar", command=self.limpiar_filtros, width=12)\
            .pack(side=tk.TOP, pady=2)


        # --- 2. Resultados (Treeview) ---
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL)
        x_scroll = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL)
        
        # Definición de columnas
        cols = ('ID', 'Fecha', 'Cuenta', 'Moneda', 'Descripcion', 'Referencia', 
                'Tercero', 'Grupo', 'Concepto', 'Valor', 'Detalle')
        
        self.tree = ttk.Treeview(result_frame, columns=cols, show='headings', 
                                 yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)
        
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Configuración de Cabeceras y Columnas
        self.tree.heading('ID', text='ID')
        self.tree.heading('Fecha', text='Fecha')
        self.tree.heading('Cuenta', text='Cuenta')
        self.tree.heading('Moneda', text='Moneda')
        self.tree.heading('Descripcion', text='Descripción Movimiento')
        self.tree.heading('Referencia', text='Referencia')
        self.tree.heading('Tercero', text='Tercero')
        self.tree.heading('Grupo', text='Grupo')
        self.tree.heading('Concepto', text='Concepto')
        self.tree.heading('Valor', text='Valor')
        self.tree.heading('Detalle', text='Detalle/Notas')
        
        # Anchos
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Fecha', width=80, anchor='center')
        self.tree.column('Cuenta', width=100)
        self.tree.column('Moneda', width=60, anchor='center')
        self.tree.column('Descripcion', width=250)
        self.tree.column('Referencia', width=100)
        self.tree.column('Tercero', width=200)
        self.tree.column('Grupo', width=120)
        self.tree.column('Concepto', width=150)
        self.tree.column('Valor', width=100, anchor='e')
        self.tree.column('Detalle', width=150)
        
        # Doble click para editar
        self.tree.bind('<Double-1>', self.abrir_editor)
        
        # --- 3. Barra de Estado y Total ---
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_bar = ttk.Label(bottom_frame, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.lbl_total = ttk.Label(bottom_frame, text="Total: $0.00", 
                                   relief=tk.SUNKEN, anchor=tk.E, font=('Arial', 10, 'bold'))
        self.lbl_total.pack(side=tk.RIGHT, padx=(10, 0), ipadx=10)

    def conectar(self):
        return psycopg2.connect(**DB_CONFIG)

    def cargar_catalogos(self):
        """Carga listas para los comboboxes del editor."""
        try:
            conn = self.conectar()
            cur = conn.cursor()
            
            # Terceros (sin descripcion/referencia - 3NF)
            cur.execute("SELECT terceroid, tercero FROM terceros WHERE activa = TRUE ORDER BY tercero")
            # Solo ID - Tercero (sin descripción)
            self.terceros_lista = [f"{t[0]} - {t[1]}" for t in cur.fetchall()]
            
            # Grupos
            cur.execute("SELECT grupoid, grupo FROM grupos ORDER BY grupo")
            self.grupos_lista = cur.fetchall() # Guardamos tupla (id, nombre) para filtrar conceptos
            
            # Conceptos
            cur.execute("SELECT conceptoid, concepto, grupoid_fk FROM conceptos ORDER BY concepto")
            self.conceptos_lista = cur.fetchall() # Guardamos tupla (id, nombre, grupoid)
            
            # Cuentas
            cur.execute("SELECT cuentaid, cuenta FROM cuentas ORDER BY cuenta")
            self.cuentas_lista = [f"{c[0]} - {c[1]}" for c in cur.fetchall()]
            
            # Monedas
            cur.execute("SELECT monedaid, moneda FROM monedas ORDER BY moneda")
            self.monedas_lista = [f"{m[0]} - {m[1]}" for m in cur.fetchall()]
            
            
            # Poblar combos de filtros
            cuentas_con_todas = ["Todas"] + self.cuentas_lista
            self.cb_filter_cuenta['values'] = cuentas_con_todas
            self.cb_filter_cuenta.set("Todas")

            self.cb_filter_tercero['values'] = self.terceros_lista
            
            nombres_grupos = [f"{g[0]} - {g[1]}" for g in self.grupos_lista]
            self.cb_filter_grupo['values'] = nombres_grupos
            
            nombres_conceptos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
            # Inicialmente todos son validos
            self.conceptos_f_validos = nombres_conceptos
            self.cb_filter_concepto['values'] = nombres_conceptos
            
            # Configurar filtrado dinámico para los combos de FILTRO
            self.setup_filtering(self.cb_filter_cuenta, cuentas_con_todas)
            self.setup_filtering(self.cb_filter_tercero, self.terceros_lista)
            self.setup_filtering(self.cb_filter_grupo, nombres_grupos)
            # Conceptos usa lambda para tener siempre la lista valida actual
            self.setup_filtering(self.cb_filter_concepto, lambda: self.conceptos_f_validos)
            
            conn.close()
        except Exception as e:
            self.mostrar_mensaje("Error", f"Error cargando catálogos: {e}", 'error')

    def buscar_movimientos(self):
        f_inicio = self.date_from.get_date()
        f_fin = self.date_to.get_date()
        texto = self.txt_search.get().strip()
        
        # Obtener IDs de filtros
        def extract_id(val):
            return int(val.split(' - ')[0]) if val and ' - ' in val else None
            
        f_cuenta = extract_id(self.cb_filter_cuenta.get())
        f_tercero = extract_id(self.cb_filter_tercero.get())
        f_grupo = extract_id(self.cb_filter_grupo.get())
        f_concepto = extract_id(self.cb_filter_concepto.get())
        
        query = """
            SELECT 
                m.Id, m.Fecha, 
                cu.cuenta, mo.moneda,
                m.Descripcion, m.Referencia,
                t.tercero,
                g.grupo, c.concepto,
                m.Valor, m.Detalle,
                m.TerceroID, m.GrupoID, m.ConceptoID, m.CuentaID, m.MonedaID
            FROM movimientos m
            LEFT JOIN terceros t ON m.TerceroID = t.terceroid
            LEFT JOIN grupos g ON m.GrupoID = g.grupoid
            LEFT JOIN conceptos c ON m.ConceptoID = c.conceptoid
            LEFT JOIN cuentas cu ON m.CuentaID = cu.cuentaid
            LEFT JOIN monedas mo ON m.MonedaID = mo.monedaid
            WHERE m.Fecha BETWEEN %s AND %s
        """
        params = [f_inicio, f_fin]
        
        if texto:
            term = f"%{texto}%"
            query += """ AND (
                m.Descripcion ILIKE %s OR 
                m.Referencia ILIKE %s OR 
                t.tercero ILIKE %s OR
                CAST(m.Valor AS TEXT) ILIKE %s
            )"""
            params.extend([term, term, term, term])

        if f_cuenta:
            query += " AND m.CuentaID = %s"
            params.append(f_cuenta)
            
        if f_tercero:
            query += " AND m.TerceroID = %s"
            params.append(f_tercero)
            
        if f_grupo:
            query += " AND m.GrupoID = %s"
            params.append(f_grupo)
            
        if f_concepto:
            query += " AND m.ConceptoID = %s"
            params.append(f_concepto)
            
        # Filtro Signo
        if self.filtro_signo == 'pos':
            query += " AND m.Valor > 0"
        elif self.filtro_signo == 'neg':
            query += " AND m.Valor < 0"
            
        query += " ORDER BY m.Fecha DESC, m.Id DESC"
        
        try:
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()
            
            # Limpiar treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if hasattr(self, 'lbl_total'):
                self.lbl_total.config(text="Total: $0.00")
                
            self.movimientos = {} # Guardar referencia para edición
            
            for row in rows:
                mid = row[0]
                self.movimientos[mid] = row # Guardamos toda la data raw
                
                # ID(0), Fecha(1), Cuenta(2), Moneda(3), Desc(4), Ref(5), 
                # TerceroNam(6), Grupo(7), Concepto(8), Valor(9), Detalle(10)
                # TerceroID(11), GrupoID(12), ConceptoID(13), CuentaID(14), MonedaID(15)
                
                # Cuenta: ID - Cuenta
                cuenta_str = f"{row[14]} - {row[2]}" if row[14] is not None else ""
                
                # Moneda: ID - Moneda
                moneda_str = f"{row[15]} - {row[3]}" if row[15] is not None else ""
                
                # Tercero: ID - Tercero (sin descripción)
                tercero_str = f"{row[11]} - {row[6]}" if row[11] is not None else ""
                
                # Grupo: ID - Grupo
                grupo_str = f"{row[12]} - {row[7]}" if row[12] is not None else ""
                
                # Concepto: ID - Concepto
                concepto_str = f"{row[13]} - {row[8]}" if row[13] is not None else ""
                
                val_str = f"${row[9]:,.2f}" if row[9] is not None else "$0.00"
                
                # Manejo de Detalle None -> ""
                detalle_str = row[10] if row[10] is not None else ""
                
                display_values = (
                    mid, row[1], cuenta_str, moneda_str, row[4], row[5], 
                    tercero_str, grupo_str, concepto_str, val_str, detalle_str
                )
                self.tree.insert('', 'end', iid=mid, values=display_values)
                
            # Calcular total general de la consulta
            total_valor = 0.0
            if rows:
                try:
                    total_valor = sum(float(r[9]) for r in rows if r[9] is not None)
                except Exception as e:
                    print(f"Error sumando total: {e}")
            
            self.status_bar.config(text=f"Total registros encontrados: {len(rows)}")
            if hasattr(self, 'lbl_total'):
                self.lbl_total.config(text=f"Total: ${total_valor:,.2f}")
            
        except Exception as e:
            self.mostrar_mensaje("Error", f"Error en búsqueda: {e}", 'error')



    def limpiar_filtros(self):
        self.txt_search.delete(0, tk.END)
        self.cb_filter_cuenta.set('')
        self.cb_filter_tercero.set('')
        self.cb_filter_grupo.set('')
        self.cb_filter_concepto.set('')
        self.filtro_signo = 'todos'
        # Reset fechas opcionalmente
        self.buscar_movimientos()

    def set_signo(self, modo):
        """Establece filtro de signo y refresca."""
        self.filtro_signo = modo
        self.buscar_movimientos()

    def set_date_range(self, mode):
        """Configura las fechas según el modo seleccionado."""
        hoy = date.today()
        
        if mode == 'this_month':
            inicio = hoy.replace(day=1)
            fin = hoy
        elif mode == 'last_month':
            # Primer dia del mes anterior
            fin = hoy.replace(day=1) - timedelta(days=1)
            inicio = fin.replace(day=1)
        elif mode == 'last_3m':
            inicio = hoy - relativedelta(months=3)
            fin = hoy
        elif mode == 'ytd':
            inicio = hoy.replace(month=1, day=1)
            fin = hoy
        elif mode == 'last_12m':
            inicio = hoy - relativedelta(years=1)
            fin = hoy
        else:
            return
            
        self.date_from.set_date(inicio)
        self.date_to.set_date(fin)
        self.buscar_movimientos()

    def seleccionar_por_id(self, combo):
        """Busca el ID ingresado en los valores del combo y lo selecciona."""
        texto = combo.get().strip()
        if not texto.isdigit():
            return
            
        search_id = int(texto)
        prefix = f"{search_id} - "
        
        # Buscar en los valores actuales del combo (que pueden estar filtrados)
        for value in combo['values']:
            if value.startswith(prefix):
                combo.set(value)
                combo.icursor(tk.END)
                return
                
        self.mostrar_mensaje("No encontrado", f"No se encontró el ID {search_id} en la lista actual.", 'warning')

    def setup_filtering(self, combo, source_list_ref):
        """
        Configura el filtrado 'mientras escribes' para un combobox.
        source_list_ref: puede ser una lista directa o un atributo (string) de self ni es variable.
                         Para hacerlo simple pasaremos una lambda que retorne la lista completa.
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

    def filtrar_conceptos_panel(self, event=None):
        """Filtra los conceptos del panel principal segun el grupo seleccionado."""
        g_str = self.cb_filter_grupo.get()
        if g_str and ' - ' in g_str:
            try:
                gid = int(g_str.split(' - ')[0])
                self.conceptos_f_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista if c[2] == gid]
            except:
                self.conceptos_f_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
        else:
             self.conceptos_f_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
        
        self.cb_filter_concepto['values'] = self.conceptos_f_validos
        self.cb_filter_concepto.set('')
        

    def abrir_editor(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        
        data = self.movimientos[int(item_id)]
        # Indices in data:
        # 0:Id, 1:Fecha, 2:CuentaNom, 3:MonedaNom, 4:Desc, 5:Ref, 
        # 6:TerceroNom, 7:GrupoNom, 8:ConceptoNom, 
        # 9:Valor, 10:Detalle, 
        # 11:TerceroID, 12:GrupoID, 13:ConceptoID, 14:CuentaID, 15:MonedaID
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar Movimiento #{data[0]}")
        
        # Dimensiones del diálogo
        d_width = 800
        d_height = 600
        
        # Obtener geometría y posición de la ventana principal
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        
        # Calcular posición centrada
        pos_x = root_x + (root_w // 2) - (d_width // 2)
        pos_y = root_y + (root_h // 2) - (d_height // 2)
        
        dialog.geometry(f"{d_width}x{d_height}+{pos_x}+{pos_y}")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # --- Formulario ---
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # ID (Readonly)
        ttk.Label(frame, text="ID:").grid(row=0, column=0, sticky=tk.W)
        entry_id = ttk.Entry(frame, state='readonly')
        entry_id.insert(0, data[0])
        entry_id.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Fecha
        ttk.Label(frame, text="Fecha:").grid(row=0, column=2, sticky=tk.W)
        entry_fecha = DateEntry(frame, date_pattern='yyyy-mm-dd')
        entry_fecha.set_date(data[1])
        entry_fecha.grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Descripción
        ttk.Label(frame, text="Descripción:").grid(row=1, column=0, sticky=tk.W)
        entry_desc = ttk.Entry(frame, width=80)
        entry_desc.insert(0, data[4])
        entry_desc.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=5)
        
        # Referencia
        ttk.Label(frame, text="Referencia:").grid(row=2, column=0, sticky=tk.W)
        entry_ref = ttk.Entry(frame, width=30)
        entry_ref.insert(0, data[5] if data[5] else "")
        entry_ref.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Valor
        ttk.Label(frame, text="Valor:").grid(row=2, column=2, sticky=tk.W)
        entry_valor = ttk.Entry(frame, width=20)
        entry_valor.insert(0, data[9])
        entry_valor.grid(row=2, column=3, sticky=tk.W, pady=5)
        
        # --- Clasificación ---
        separator = ttk.Separator(frame, orient='horizontal')
        separator.grid(row=3, column=0, columnspan=4, sticky='ew', pady=15)
        ttk.Label(frame, text="Clasificación", font=('Arial', 10, 'bold')).grid(row=3, column=0, pady=(15,0))

        # Tercero
        ttk.Label(frame, text="Tercero:").grid(row=4, column=0, sticky=tk.W)
        combo_tercero = ttk.Combobox(frame, values=self.terceros_lista, width=50)
        combo_tercero.grid(row=4, column=1, columnspan=3, sticky=tk.W, pady=5)
        combo_tercero.bind('<Return>', lambda e: self.seleccionar_por_id(combo_tercero))
        self.setup_filtering(combo_tercero, self.terceros_lista)
        
        # Set current value
        if data[11]: # TerceroID
            current_t = next((t for t in self.terceros_lista if t.startswith(f"{data[11]} -")), "")
            combo_tercero.set(current_t)
            
        # Cuenta
        ttk.Label(frame, text="Cuenta:").grid(row=5, column=0, sticky=tk.W)
        combo_cuenta = ttk.Combobox(frame, values=self.cuentas_lista, width=30)
        combo_cuenta.grid(row=5, column=1, sticky=tk.W, pady=5)
        combo_cuenta.bind('<Return>', lambda e: self.seleccionar_por_id(combo_cuenta))
        self.setup_filtering(combo_cuenta, self.cuentas_lista)
        
        if data[14]:
            current_c = next((c for c in self.cuentas_lista if c.startswith(f"{data[14]} -")), "")
            combo_cuenta.set(current_c)

        # Moneda
        ttk.Label(frame, text="Moneda:").grid(row=5, column=2, sticky=tk.W)
        combo_moneda = ttk.Combobox(frame, values=self.monedas_lista, width=20)
        combo_moneda.grid(row=5, column=3, sticky=tk.W, pady=5)
        combo_moneda.bind('<Return>', lambda e: self.seleccionar_por_id(combo_moneda))
        self.setup_filtering(combo_moneda, self.monedas_lista)
        
        if data[15]:
            current_m = next((m for m in self.monedas_lista if m.startswith(f"{data[15]} -")), "")
            combo_moneda.set(current_m)

        # Grupo
        ttk.Label(frame, text="Grupo:").grid(row=6, column=0, sticky=tk.W)
        nombres_grupos = [f"{g[0]} - {g[1]}" for g in self.grupos_lista]
        combo_grupo = ttk.Combobox(frame, values=nombres_grupos, width=30)
        combo_grupo.grid(row=6, column=1, sticky=tk.W, pady=5)
        # Se vincula abajo después de definir update_conceptos
        self.setup_filtering(combo_grupo, nombres_grupos)
        
        if data[12]: # GrupoID
            current_g = next((g for g in nombres_grupos if g.startswith(f"{data[12]} -")), "")
            combo_grupo.set(current_g)

        # Concepto
        ttk.Label(frame, text="Concepto:").grid(row=6, column=2, sticky=tk.W)
        combo_concepto = ttk.Combobox(frame, width=30) # Valores dependen del grupo
        combo_concepto.grid(row=6, column=3, sticky=tk.W, pady=5)
        combo_concepto.bind('<Return>', lambda e: self.seleccionar_por_id(combo_concepto))
        
        # Guardaremos la lista actual de conceptos válidos para el editor
        conceptos_editor_validos = []

        # Función para filtrar conceptos (Cambio de grupo)
        def update_conceptos(event=None):
            nonlocal conceptos_editor_validos
            g_str = combo_grupo.get()
            if g_str and ' - ' in g_str:
                gid = int(g_str.split(' - ')[0])
                conceptos_editor_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista if c[2] == gid]
            else:
                conceptos_editor_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
            
            combo_concepto['values'] = conceptos_editor_validos
            combo_concepto.set('') # Limpiar al cambiar grupo
                
        combo_grupo.bind('<<ComboboxSelected>>', update_conceptos)
        
        def on_editor_grupo_enter(e):
             self.seleccionar_por_id(combo_grupo)
             update_conceptos()
             
        combo_grupo.bind('<Return>', on_editor_grupo_enter)
        
        # Setup filtering for concept -> depends on current valid list
        self.setup_filtering(combo_concepto, lambda: conceptos_editor_validos)
        
        # Init values
        if data[13]: # Pre-existing group logic
             current_g = next((g for g in nombres_grupos if g.startswith(f"{data[13]} -")), "") # Redundant look up but ok
             # update_conceptos will act on the combobox value
             
        # Manual init of concept list based on current Group ID in data
        if data[12]:
             conceptos_editor_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista if c[2] == data[12]]
        else:
             conceptos_editor_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
             
        combo_concepto['values'] = conceptos_editor_validos

        if data[13]: # ConceptoID
            current_con = next((c for c in combo_concepto['values'] if c.startswith(f"{data[13]} -")), "")
            combo_concepto.set(current_con)

        # Detalle / Notas
        ttk.Label(frame, text="Detalle/Notas:").grid(row=7, column=0, sticky=tk.W)
        entry_detalle = ttk.Entry(frame, width=80)
        entry_detalle.insert(0, data[10] if data[10] else "")
        entry_detalle.grid(row=7, column=1, columnspan=3, sticky=tk.W, pady=5)
        
        # Botones
        btn_frame = ttk.Frame(frame, padding="20")
        btn_frame.grid(row=8, column=0, columnspan=4)
        
        def guardar():
            try:
                # Obtener IDs de los combos
                def get_id(combo_val):
                    return int(combo_val.split(' - ')[0]) if combo_val else None
                
                new_date = entry_fecha.get_date()
                new_desc = entry_desc.get().strip()
                new_ref = entry_ref.get().strip()
                new_val = float(entry_valor.get())
                new_tid = get_id(combo_tercero.get())
                new_gid = get_id(combo_grupo.get())
                new_cid = get_id(combo_concepto.get())
                new_uid = get_id(combo_cuenta.get())
                new_mid = get_id(combo_moneda.get())
                new_det = entry_detalle.get().strip()
                
                query_upd = """
                    UPDATE movimientos 
                    SET Fecha=%s, Descripcion=%s, Referencia=%s, Valor=%s, 
                        TerceroID=%s, GrupoID=%s, ConceptoID=%s, CuentaID=%s, MonedaID=%s, Detalle=%s
                    WHERE Id=%s
                """
                
                conn = self.conectar()
                cur = conn.cursor()
                cur.execute(query_upd, (
                    new_date, new_desc, new_ref, new_val,
                    new_tid, new_gid, new_cid, new_uid, new_mid, new_det,
                    data[0]
                ))
                conn.commit()
                conn.close()
                
                self.mostrar_mensaje("Éxito", "Movimiento actualizado correctamente", 'success')
                dialog.destroy()
                self.buscar_movimientos() # Refrescar lista
                
            except ValueError:
                self.mostrar_mensaje("Error", "Por favor verifique los formatos numéricos y selecciones", 'error')
            except Exception as e:
                self.mostrar_mensaje("Error", f"Fallo al guardar: {e}", 'error')

        ttk.Button(btn_frame, text="💾 Guardar Cambios", command=guardar).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="❌ Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ConsultarMovimientosGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Error fatal: {e}")
        input("Presione Enter para salir...")
