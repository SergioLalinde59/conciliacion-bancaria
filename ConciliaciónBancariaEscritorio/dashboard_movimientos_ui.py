#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Movimientos - Gastos SLB
Tablero de control visual para análisis de gastos e ingresos.
Incluye KPIs, gráficos y resúmenes tabulares agrupados.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import pandas as pd
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkcalendar import DateEntry

# Configurar backend de matplotlib para Tkinter
matplotlib.use("TkAgg")

# Configuración de base de datos (compartida)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

class DashboardMovimientosUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard Financiero - Gastos SLB")
        self.root.geometry("1400x900")
        
        self.df_movimientos = pd.DataFrame()
        self.cuentas_lista = []
        self.terceros_lista = []
        self.grupos_lista = [] # Tuplas (id, nombre)
        self.conceptos_lista = [] # Tuplas (id, nombre, grupoid)
        
        # Filtros de estado
        self.var_excluir_traslados = tk.BooleanVar(value=True)
        self.var_excluir_compras = tk.BooleanVar(value=True)
        self.filtro_signo = 'todos' # 'todos', 'pos', 'neg'
        
        # Estilos
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("KPI.TLabel", font=('Arial', 20, 'bold'), foreground='navy')
        self.style.configure("KPITitle.TLabel", font=('Arial', 10), foreground='gray')
        
        self.setup_ui()
        self.cargar_catalogos()
        self.actualizar_dashboard()

    def conectar(self):
        return psycopg2.connect(**DB_CONFIG)

    def setup_ui(self):
        # --- Frame Principal ---
        main_layout = ttk.Frame(self.root, padding="15")
        main_layout.pack(fill=tk.BOTH, expand=True)

        # === 1. HEADER: FILTROS ===
        filter_frame = ttk.LabelFrame(main_layout, text="Opciones de Visualización y Filtros", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 15))

        # Contenedor filtros - Fila 0 (Botones Rápidos Fecha)
        row0 = ttk.Frame(filter_frame)
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

        # Contenedor filtros - Fila 1
        row1 = ttk.Frame(filter_frame)
        row1.pack(fill=tk.X, pady=(0, 5))

        # Fechas
        ttk.Label(row1, text="Desde:").pack(side=tk.LEFT)
        self.date_from = DateEntry(row1, width=12, background='darkblue', 
                                 foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        today = date.today()
        first_day = today.replace(day=1)
        self.date_from.set_date(first_day)
        self.date_from.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1, text="Hasta:").pack(side=tk.LEFT, padx=(15, 0))
        self.date_to = DateEntry(row1, width=12, background='darkblue', 
                               foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_to.set_date(today)
        self.date_to.pack(side=tk.LEFT, padx=5)

        # Cuenta
        ttk.Label(row1, text="Cuenta:").pack(side=tk.LEFT, padx=(15, 0))
        self.cb_cuenta = ttk.Combobox(row1, width=25)
        self.cb_cuenta.pack(side=tk.LEFT, padx=5)
        self.cb_cuenta.bind('<Return>', lambda e: self.seleccionar_por_id(self.cb_cuenta)) # Support ID selection

        # Checkbox Excluir Traslados
        self.chk_traslados = ttk.Checkbutton(row1, text="Excluir Traslados", variable=self.var_excluir_traslados, command=self.actualizar_dashboard)
        self.chk_traslados.pack(side=tk.LEFT, padx=(15, 0))

        # Checkbox Excluir Compras (TC)
        self.chk_compras = ttk.Checkbutton(row1, text="Excluir Compras", variable=self.var_excluir_compras, command=self.actualizar_dashboard)
        self.chk_compras.pack(side=tk.LEFT, padx=(5, 0))

        # Botones
        ttk.Button(row1, text="🔄 Actualizar", command=self.actualizar_dashboard)\
            .pack(side=tk.RIGHT, padx=5)
        ttk.Button(row1, text="🧹 Limpiar", command=self.limpiar_filtros)\
            .pack(side=tk.RIGHT, padx=5)

        # Contenedor filtros - Fila 2
        row2 = ttk.Frame(filter_frame)
        row2.pack(fill=tk.X)

        # Tercero
        ttk.Label(row2, text="Tercero:").pack(side=tk.LEFT)
        self.cb_tercero = ttk.Combobox(row2, width=30)
        self.cb_tercero.pack(side=tk.LEFT, padx=5)
        self.cb_tercero.bind('<Return>', lambda e: self.seleccionar_por_id(self.cb_tercero))

        # Grupo
        ttk.Label(row2, text="Grupo:").pack(side=tk.LEFT, padx=(15, 0))
        self.cb_grupo = ttk.Combobox(row2, width=20)
        self.cb_grupo.pack(side=tk.LEFT, padx=5)
        
        # Concepto
        ttk.Label(row2, text="Concepto:").pack(side=tk.LEFT, padx=(15, 0))
        self.cb_concepto = ttk.Combobox(row2, width=20)
        self.cb_concepto.pack(side=tk.LEFT, padx=5)
        self.cb_concepto.bind('<Return>', lambda e: self.seleccionar_por_id(self.cb_concepto))
        
        # Logica Grupo -> Concepto
        def on_grupo_enter(e):
            self.seleccionar_por_id(self.cb_grupo)
            self.filtrar_conceptos_panel()
            
        self.cb_grupo.bind('<Return>', on_grupo_enter)
        self.cb_grupo.bind('<<ComboboxSelected>>', self.filtrar_conceptos_panel)
        
        # Lista local para conceptos filtrados
        self.conceptos_f_validos = [] 

        # === 2. AREA DE KPIs ===
        kpi_frame = ttk.Frame(main_layout)
        kpi_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Helper para crear tarjetas KPI
        def create_kpi_card(parent, title, var_name, color):
            card = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            ttk.Label(card, text=title, style="KPITitle.TLabel", padding=(10, 10, 10, 0)).pack(anchor=tk.W)
            lbl = ttk.Label(card, text="$ 0.00", style="KPI.TLabel", padding=(10, 0, 10, 10), foreground=color)
            lbl.pack(anchor=tk.W)
            setattr(self, var_name, lbl)
            return card

        create_kpi_card(kpi_frame, "Total Movimientos (Selección)", "lbl_kpi_total", "#2c3e50")
        create_kpi_card(kpi_frame, "Total Grupos Activos", "lbl_kpi_grupos", "#e67e22")
        create_kpi_card(kpi_frame, "Promedio Diario", "lbl_kpi_promedio", "#27ae60")

        # === 3. CONTENIDO PRINCIPAL (PanedWindow para separar Gráficos de Tablas) ===
        # Orientación vertical: Arriba gráficos, Abajo tablas detalle
        paned = ttk.PanedWindow(main_layout, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- A. FRAME GRÁFICOS (Arriba) ---
        graphs_frame = ttk.Frame(paned)
        paned.add(graphs_frame, weight=3) # Mayor peso para gráficos

        # Dividir gráficos en Izq (Pie Grupos) y Der (Barras Conceptos)
        graphs_frame.columnconfigure(0, weight=1)
        graphs_frame.columnconfigure(1, weight=1)
        graphs_frame.rowconfigure(0, weight=1)

        # Gráfico 1
        self.fig_grupos = Figure(figsize=(5, 4), dpi=100)
        self.ax_grupos = self.fig_grupos.add_subplot(111)
        self.canvas_grupos = FigureCanvasTkAgg(self.fig_grupos, master=graphs_frame)
        self.canvas_grupos.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5)

        # Gráfico 2
        self.fig_conceptos = Figure(figsize=(5, 4), dpi=100)
        self.ax_conceptos = self.fig_conceptos.add_subplot(111)
        self.canvas_conceptos = FigureCanvasTkAgg(self.fig_conceptos, master=graphs_frame)
        self.canvas_conceptos.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=5)

        # --- B. FRAME TABLAS DE RESUMEN (Abajo) ---
        tables_frame = ttk.Frame(paned)
        paned.add(tables_frame, weight=2)
        
        # Tabs para diferentes vistas de resumen
        self.notebook = ttk.Notebook(tables_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Tab: Por Grupo
        self.tab_grupo = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_grupo, text="Resumen por Grupo")
        self.tree_grupo = self._crear_treeview(self.tab_grupo, columns=("Grupo", "Total", "Conteo", "% del Total"))

        # Tab: Por Concepto
        self.tab_concepto = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_concepto, text="Resumen por Concepto")
        self.tree_concepto = self._crear_treeview(self.tab_concepto, columns=("Concepto", "Grupo", "Total", "Conteo"))
        
        # Tab: Por Tercero (Bonus)
        self.tab_tercero = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tercero, text="Top Terceros")
        self.tree_tercero = self._crear_treeview(self.tab_tercero, columns=("Tercero", "Total", "Conteo"))


    def _crear_treeview(self, parent, columns):
        # Scrollbars
        y_scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        # Tree
        tree = ttk.Treeview(parent, columns=columns, show='headings', yscrollcommand=y_scroll.set)
        y_scroll.config(command=tree.yview)
        
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Configurar columnas
        for col in columns:
            tree.heading(col, text=col)
            # Ajuste básico de anchos
            if col in ["Total", "Conteo", "% del Total"]:
                tree.column(col, width=100, anchor='e')
            else:
                tree.column(col, width=200, anchor='w')
                
        return tree

    def cargar_catalogos(self):
        try:
            conn = self.conectar()
            cur = conn.cursor()
            
            # Cuentas
            cur.execute("SELECT cuentaid, cuenta FROM cuentas ORDER BY cuenta")
            self.cuentas_lista = [f"{c[0]} - {c[1]}" for c in cur.fetchall()]
            
            # Terceros
            cur.execute("SELECT terceroid, tercero FROM terceros ORDER BY tercero")
            self.terceros_lista = [f"{t[0]} - {t[1]}" for t in cur.fetchall()]
            
            # Grupos
            cur.execute("SELECT grupoid, grupo FROM grupos ORDER BY grupo")
            self.grupos_lista = cur.fetchall() # Tuple (id, name)
            
            # Conceptos
            cur.execute("SELECT conceptoid, concepto, grupoid_fk FROM conceptos ORDER BY concepto")
            self.conceptos_lista = cur.fetchall() # Tuple (id, name, grupoid)
            
            conn.close()
            
            # 1. Setup Cuentas
            cuentas_plus = ["Todas"] + self.cuentas_lista
            self.cb_cuenta['values'] = cuentas_plus
            self.cb_cuenta.set("Todas")
            self.setup_filtering(self.cb_cuenta, cuentas_plus)
            
            # 2. Setup Terceros
            self.cb_tercero['values'] = self.terceros_lista
            self.setup_filtering(self.cb_tercero, self.terceros_lista)
            
            # 3. Setup Grupos
            nombres_grupos = [f"{g[0]} - {g[1]}" for g in self.grupos_lista]
            self.cb_grupo['values'] = nombres_grupos
            self.setup_filtering(self.cb_grupo, nombres_grupos)
            
            # 4. Setup Conceptos
            # Inicialmente todos
            self.conceptos_f_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
            self.cb_concepto['values'] = self.conceptos_f_validos
            # Lambda para tener siempre la lista valida actual
            self.setup_filtering(self.cb_concepto, lambda: self.conceptos_f_validos)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando catálogos: {e}")

    def limpiar_filtros(self):
        """Resetea todos los filtros a su estado inicial."""
        # Reset fechas (Inicio de mes - Hoy)
        today = date.today()
        first_day = today.replace(day=1)
        self.date_from.set_date(first_day)
        self.date_to.set_date(today)
        
        # Reset combos
        self.cb_cuenta.set("Todas")
        self.cb_tercero.set("")
        self.cb_grupo.set("")
        self.cb_concepto.set("")
        self.var_excluir_traslados.set(True)
        self.var_excluir_compras.set(True)
        self.filtro_signo = 'todos'
        
        # Reset lista conceptos filtrados a todos
        self.conceptos_f_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
        self.cb_concepto['values'] = self.conceptos_f_validos
        
        # Actualizar vista
        self.actualizar_dashboard()

    def set_signo(self, modo):
        """Establece filtro de signo y refresca."""
        self.filtro_signo = modo
        self.actualizar_dashboard()

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
        self.actualizar_dashboard()

    def seleccionar_por_id(self, combo):
        """Busca el ID ingresado en los valores del combo y lo selecciona."""
        texto = combo.get().strip()
        if not texto.isdigit():
            return
            
        search_id = int(texto)
        prefix = f"{search_id} - "
        
        # Buscar en los valores actuales del combo
        for value in combo['values']:
            if value.startswith(prefix):
                combo.set(value)
                combo.icursor(tk.END)
                return
                
        messagebox.showwarning("No encontrado", f"No se encontró el ID {search_id} en la lista actual.")

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

    def filtrar_conceptos_panel(self, event=None):
        """Filtra los conceptos segun el grupo seleccionado."""
        g_str = self.cb_grupo.get()
        if g_str and ' - ' in g_str:
            try:
                gid = int(g_str.split(' - ')[0])
                self.conceptos_f_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista if c[2] == gid]
            except:
                self.conceptos_f_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
        else:
             self.conceptos_f_validos = [f"{c[0]} - {c[1]}" for c in self.conceptos_lista]
        
        self.cb_concepto['values'] = self.conceptos_f_validos
        self.cb_concepto.set('')

    def actualizar_dashboard(self):
        # 1. Obtener filtros
        f_inicio = self.date_from.get_date()
        f_fin = self.date_to.get_date()
        
        # Helpers para obtener ID
        def get_id(val):
            return int(val.split(' - ')[0]) if val and ' - ' in val else None
            
        cuenta_id = get_id(self.cb_cuenta.get()) if self.cb_cuenta.get() != "Todas" else None
        tercero_id = get_id(self.cb_tercero.get())
        grupo_id = get_id(self.cb_grupo.get())
        concepto_id = get_id(self.cb_concepto.get())
        
        # 2. Query Data con Psycopg2 (luego a Pandas)
        query = """
            SELECT 
                m.Id, m.Fecha, m.Valor,
                CASE WHEN g.grupoid IS NOT NULL THEN CAST(g.grupoid AS TEXT) || ' - ' || g.grupo ELSE 'Sin Grupo' END as grupo,
                CASE WHEN c.conceptoid IS NOT NULL THEN CAST(c.conceptoid AS TEXT) || ' - ' || c.concepto ELSE 'Sin Concepto' END as concepto,
                CASE WHEN t.terceroid IS NOT NULL THEN CAST(t.terceroid AS TEXT) || ' - ' || t.tercero ELSE 'Sin Tercero' END as tercero,
                cu.cuenta
            FROM movimientos m
            LEFT JOIN grupos g ON m.GrupoID = g.grupoid
            LEFT JOIN conceptos c ON m.ConceptoID = c.conceptoid
            LEFT JOIN terceros t ON m.TerceroID = t.terceroid
            LEFT JOIN cuentas cu ON m.CuentaID = cu.cuentaid
            WHERE m.Fecha BETWEEN %s AND %s
        """
        params = [f_inicio, f_fin]
        
        if cuenta_id:
            query += " AND m.CuentaID = %s"
            params.append(cuenta_id)
            
        if tercero_id:
            query += " AND m.TerceroID = %s"
            params.append(tercero_id)
            
        if grupo_id:
            query += " AND m.GrupoID = %s"
            params.append(grupo_id)
            
        if concepto_id:
            query += " AND m.ConceptoID = %s"
            params.append(concepto_id)
            
        # Filtro de Traslados (Grupo 47)
        if self.var_excluir_traslados.get():
            query += " AND (m.GrupoID <> 47 OR m.GrupoID IS NULL)"

        # Filtro de Compras Especificas
        if self.var_excluir_compras.get():
            query += """ AND NOT (
                (m.GrupoID = 4 AND m.ConceptoID = 20) OR 
                (m.GrupoID = 149 AND m.ConceptoID = 26) OR 
                (m.GrupoID = 199 AND m.ConceptoID = 27)
            )"""

        # Filtro Signo
        if self.filtro_signo == 'pos':
            query += " AND m.Valor > 0"
        elif self.filtro_signo == 'neg':
            query += " AND m.Valor < 0"

        try:
            conn = self.conectar()
            # Usar pandas directo para SQL es más cómodo
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            self.df_movimientos = df
            
            # Procesar datos y actualizar UI
            self._actualizar_kpis()
            self._actualizar_graficos()
            self._actualizar_tablas()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error actualizando dashboard: {e}")
            import traceback
            traceback.print_exc()

    def _actualizar_kpis(self):
        if self.df_movimientos.empty:
            total = 0
            n_grupos = 0
            promedio = 0
        else:
            total = self.df_movimientos['valor'].sum()
            n_grupos = self.df_movimientos['grupo'].nunique()
            
            # Promedio diario
            dias = (self.date_to.get_date() - self.date_from.get_date()).days + 1
            promedio = total / dias if dias > 0 else 0
            
        self.lbl_kpi_total.config(text=f"${total:,.2f}")
        self.lbl_kpi_grupos.config(text=f"{n_grupos}")
        self.lbl_kpi_promedio.config(text=f"${promedio:,.2f} / día")

    def _actualizar_graficos(self):
        # Limpiar figuras
        self.ax_grupos.clear()
        self.ax_conceptos.clear()
        
        if self.df_movimientos.empty:
            self.canvas_grupos.draw()
            self.canvas_conceptos.draw()
            return

        # --- Lógica dinámica según el filtro de signo ---
        # Si el usuario eligió 'pos' (Ingresos), graficamos ingresos.
        # Si eligió 'neg' (Gastos) o 'todos' (Default), graficamos gastos.

        modo_ingreso = (self.filtro_signo == 'pos')
        
        if modo_ingreso:
            df_target = self.df_movimientos[self.df_movimientos['valor'] > 0].copy()
            titulo_pie = "Distribución de INGRESOS por Grupo"
            titulo_bar = "Top 10 Conceptos (Mayores INGRESOS)"
            color_bar = '#27ae60' # Verde
        else:
            # Gastos (o todos, graficamos la parte negativa)
            df_target = self.df_movimientos[self.df_movimientos['valor'] < 0].copy()
            titulo_pie = "Distribución de GASTOS por Grupo"
            titulo_bar = "Top 10 Conceptos (Mayor GASTO)"
            color_bar = '#e74c3c' # Rojo

        if df_target.empty:
            msg = "Sin ingresos registrados" if modo_ingreso else "Sin gastos registrados"
            self.ax_grupos.text(0.5, 0.5, msg, ha='center')
            self.ax_conceptos.text(0.5, 0.5, msg, ha='center')
            self.canvas_grupos.draw()
            self.canvas_conceptos.draw()
            return
            
        # Convertir a positivo para graficar magnitud
        df_target['valor_abs'] = df_target['valor'].abs()
            
        # --- Gráfico 1: Pie Grupos ---
        df_g = df_target.groupby('grupo')['valor_abs'].sum().sort_values(ascending=False)
        
        # Tomar top 8 y agrupar resto en "Otros"
        if len(df_g) > 8:
            otros = df_g.iloc[8:].sum()
            df_g = df_g.iloc[:8]
            df_g['Otros'] = otros
            
        # Colores
        colors = matplotlib.colormaps['tab20c'](range(len(df_g)))

        wedges, texts, autotexts = self.ax_grupos.pie(
            df_g, labels=df_g.index, autopct='%1.1f%%', 
            startangle=140, colors=colors, textprops={'fontsize': 8}
        )
        self.ax_grupos.set_title(titulo_pie, fontsize=10, fontweight='bold')
        
        # --- Gráfico 2: Bar Conceptos (Top 10) ---
        df_c = df_target.groupby('concepto')['valor_abs'].sum().sort_values(ascending=True).tail(10)
        
        bars = self.ax_conceptos.barh(df_c.index, df_c.values, color=color_bar) 
        self.ax_conceptos.set_title(titulo_bar, fontsize=10, fontweight='bold')
        self.ax_conceptos.tick_params(axis='y', labelsize=8)
        self.ax_conceptos.tick_params(axis='x', labelsize=8)
        
        # Formatear eje X como moneda (abreviada)
        def human_format(num, pos):
            magnitude = 0
            while abs(num) >= 1000:
                magnitude += 1
                num /= 1000.0
            return '%.1f%s' % (num, ['', 'K', 'M', 'G'][magnitude])

        self.ax_conceptos.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(human_format))
        
        self.fig_grupos.tight_layout()
        self.fig_conceptos.tight_layout()
        
        self.canvas_grupos.draw()
        self.canvas_conceptos.draw()

    def _actualizar_tablas(self):
        # Limpiar tablas
        for tree in [self.tree_grupo, self.tree_concepto, self.tree_tercero]:
            for item in tree.get_children():
                tree.delete(item)
                
        if self.df_movimientos.empty:
            return
            
        total_global = self.df_movimientos['valor'].sum() or 1 # Evitar div/0

        # --- Tabla 1: Por Grupo ---
        df_g = self.df_movimientos.groupby('grupo')['valor'].agg(['sum', 'count']).reset_index()
        df_g = df_g.sort_values(by='sum', ascending=False)
        
        for _, row in df_g.iterrows():
            pct = (row['sum'] / total_global) * 100
            vals = (row['grupo'], f"${row['sum']:,.2f}", int(row['count']), f"{pct:.1f}%")
            self.tree_grupo.insert('', 'end', values=vals)

        # --- Tabla 2: Por Concepto ---
        # Incluimos el grupo al que pertenece el concepto para contexto
        # Suponemos que un concepto pertenece a un grupo predominante si hay ambigüedad, 
        # pero en la BD es M:1 por movimiento. 
        # Agrupamos por Concepto y Grupo
        df_c = self.df_movimientos.groupby(['concepto', 'grupo'])['valor'].agg(['sum', 'count']).reset_index()
        df_c = df_c.sort_values(by='sum', ascending=False)
        
        for _, row in df_c.iterrows():
            vals = (row['concepto'], row['grupo'], f"${row['sum']:,.2f}", int(row['count']))
            self.tree_concepto.insert('', 'end', values=vals)
            
        # --- Tabla 3: Por Tercero ---
        df_t = self.df_movimientos.groupby('tercero')['valor'].agg(['sum', 'count']).reset_index()
        df_t = df_t.sort_values(by='sum', ascending=False)
        
        for _, row in df_t.iterrows():
            vals = (row['tercero'], f"${row['sum']:,.2f}", int(row['count']))
            self.tree_tercero.insert('', 'end', values=vals)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DashboardMovimientosUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Error fatal: {e}")
