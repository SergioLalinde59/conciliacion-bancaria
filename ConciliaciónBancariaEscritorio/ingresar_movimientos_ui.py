#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingreso Manual de Movimientos - Interfaz Gráfica
Permite ingresar manualmente gastos en efectivo y otros movimientos a la base de datos.
Versión simplificada: Sin descripción/referencia manual, sin tabla de recientes.

Autor: Antigravity
Fecha: 2025-12-31
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import psycopg2
from datetime import datetime
from tkcalendar import DateEntry

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}

class IngresarMovimientosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ingreso Manual de Movimientos")
        self.root.geometry("800x600") # Reducido ya que quitamos la tabla lateral
        self.root.resizable(True, True)
        
        # Variables de estado
        self.tercero_seleccionado_id = None
        self.grupo_seleccionado_id = None
        self.concepto_seleccionado_id = None
        
        # Datos en memoria
        self.lista_grupos_formato = []
        self.conceptos_completos = []
        
        # Estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.setup_ui()
        
        # Cargar datos iniciales
        self.cargar_datos_iniciales()
        self.agregar_log("✓ Aplicación iniciada. Formulario simplificado listo.", 'success')

    def setup_ui(self):
        """Configura la interfaz gráfica."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Ingresar Nuevo Movimiento", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # --- FORMULARIO CENTRAL ---
        form_frame = ttk.LabelFrame(main_frame, text="Datos del Gasto / Movimiento", padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Grid para formulario
        grid_opts = {'sticky': tk.W, 'pady': 12, 'padx': 5}
        
        # Fila 0: Fecha y Cuenta
        ttk.Label(form_frame, text="Fecha:").grid(row=0, column=0, **grid_opts)
        self.date_entry = DateEntry(form_frame, width=15, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_entry.grid(row=0, column=1, **grid_opts)
        
        ttk.Label(form_frame, text="Cuenta:").grid(row=0, column=2, **grid_opts)
        self.cuenta_combo = ttk.Combobox(form_frame, width=25, state="readonly")
        self.cuenta_combo.grid(row=0, column=3, **grid_opts)
        
        # Fila 1: Valor y Moneda
        ttk.Label(form_frame, text="Valor:").grid(row=1, column=0, **grid_opts)
        # Entry para Validar solo números y formatear
        self.valor_entry = ttk.Entry(form_frame, width=18)
        self.valor_entry.grid(row=1, column=1, **grid_opts)
        # Bind FocusOut para formatear moneda visualmente si se desea, por ahora simple
        
        ttk.Label(form_frame, text="Moneda:").grid(row=1, column=2, **grid_opts)
        self.moneda_combo = ttk.Combobox(form_frame, width=10, state="readonly")
        self.moneda_combo.grid(row=1, column=3, **grid_opts)
        
        # Separador estético
        ttk.Separator(form_frame, orient='horizontal').grid(row=2, column=0, columnspan=4, sticky='ew', pady=15)
        
        # Fila 2: Tercero (Ancho completo)
        ttk.Label(form_frame, text="Tercero:").grid(row=3, column=0, **grid_opts)
        self.tercero_combo = ttk.Combobox(form_frame, width=50) # Ancho aumentado
        self.tercero_combo.grid(row=3, column=1, columnspan=3, **grid_opts)
        
        # Fila 3: Grupo y Concepto
        ttk.Label(form_frame, text="Grupo:").grid(row=4, column=0, **grid_opts)
        self.grupo_combo = ttk.Combobox(form_frame, width=25)
        self.grupo_combo.grid(row=4, column=1, **grid_opts)
        
        ttk.Label(form_frame, text="Concepto:").grid(row=4, column=2, **grid_opts)
        self.concepto_combo = ttk.Combobox(form_frame, width=25)
        self.concepto_combo.grid(row=4, column=3, **grid_opts)
        
        # Fila 4: Detalle (Ancho completo)
        ttk.Label(form_frame, text="Detalle:").grid(row=5, column=0, **grid_opts)
        self.detalle_entry = ttk.Entry(form_frame, width=54)
        self.detalle_entry.grid(row=5, column=1, columnspan=3, **grid_opts)
        
        # Botones de Acción
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=6, column=0, columnspan=4, pady=30)
        
        self.btn_guardar = ttk.Button(btn_frame, text="💾 Guardar Movimiento", command=self.guardar_movimiento)
        self.btn_guardar.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(btn_frame, text="🧹 Limpiar", command=self.limpiar_formulario).pack(side=tk.LEFT, padx=10)
        
        # === SECCIÓN LOG (Inferior) ===
        log_frame = ttk.LabelFrame(main_frame, text="Log de Actividad", padding="5")
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, font=('Courier', 9), state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('info', foreground='blue')

        # === BINDINGS PARA SELECCIÓN POR ID ===
        self.tercero_combo.bind('<Return>', lambda e: self.seleccionar_por_id(self.tercero_combo))
        self.grupo_combo.bind('<Return>', lambda e: self.seleccionar_por_id(self.grupo_combo, es_grupo=True))
        self.concepto_combo.bind('<Return>', lambda e: self.seleccionar_por_id(self.concepto_combo))


    def seleccionar_por_id(self, combo, es_grupo=False):
        """Permite seleccionar un item escribiendo solo su ID y presionando Enter."""
        texto = combo.get().strip()
        if not texto: return

        # Si ya contiene ':', asumimos que es correcto o que el usuario ya seleccionó
        # Pero si el usuario borró parte y solo queda ID, permitimos re-buscar
        posible_id = texto.split(':')[0]
        
        if posible_id.isdigit():
            id_buscado = posible_id
            valores = combo['values']
            # Buscar el item que empieza con 'ID:'
            match = next((v for v in valores if v.startswith(f"{id_buscado}:")), None)
            
            if match:
                combo.set(match)
                combo.icursor(tk.END) # Mover cursor al final
                combo.selection_clear()
                
                # Si es grupo, disparar cascada
                if es_grupo:
                    self.on_grupo_seleccionado(None)
            else:
                # Opcional: Feedback visual de "No encontrado"
                pass

    def cargar_datos_iniciales(self):
        """Carga datos de los combos desde BD."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # 1. Cuentas
            cursor.execute("SELECT cuentaid, cuenta FROM cuentas ORDER BY cuentaid")
            cuentas = cursor.fetchall()
            valores_cuenta = [f"{c[0]}: {c[1]}" for c in cuentas]
            self.cuenta_combo['values'] = valores_cuenta
            if valores_cuenta:
                self.cuenta_combo.current(0)
            
            # 2. Monedas
            cursor.execute("SELECT monedaid, isocode FROM monedas ORDER BY monedaid")
            monedas = cursor.fetchall()
            valores_moneda = [f"{m[0]}: {m[1]}" for m in monedas]
            self.moneda_combo['values'] = valores_moneda
            # Default to COP (ID 1)
            cop = next((m for m in valores_moneda if m.startswith('1:')), None)
            if cop:
                self.moneda_combo.set(cop)
            
            # 3. Terceros (sin descripcion/referencia - 3NF)
            cursor.execute("SELECT terceroid, tercero FROM terceros WHERE activa = TRUE ORDER BY tercero")
            terceros = cursor.fetchall()
            self.lista_terceros_formato = [f"{t[0]}: {t[1]}" for t in terceros]
            self.tercero_combo['values'] = self.lista_terceros_formato
            self.setup_filtering(self.tercero_combo, self.lista_terceros_formato)
            
            # 4. Grupos y Conceptos
            cursor.execute("SELECT grupoid, grupo FROM grupos ORDER BY grupo")
            grupos = cursor.fetchall()
            self.lista_grupos_formato = [f"{g[0]}: {g[1]}" for g in grupos]
            self.grupo_combo['values'] = self.lista_grupos_formato
            self.setup_filtering(self.grupo_combo, self.lista_grupos_formato)
            
            cursor.execute("SELECT conceptoid, concepto, grupoid_fk FROM conceptos ORDER BY concepto")
            self.conceptos_completos = cursor.fetchall()
            
            # Bindings for cascading
            self.grupo_combo.bind('<<ComboboxSelected>>', self.on_grupo_seleccionado)
            
            # Configurar filtrado conceptos
            self.setup_filtering(self.concepto_combo, self.get_conceptos_validos)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.agregar_log(f"Error cargando datos: {e}", 'error')

    def setup_filtering(self, combo, source_data_or_callable):
        """Configura el filtrado dinámico para un combobox."""
        def on_keyrelease(event):
            # Si la tecla es Enter, Arrow keys, etc, ignorar para no interrumpir navegación
            if event.keysym in ('Return', 'Up', 'Down', 'Left', 'Right', 'Tab'):
                return

            value = event.widget.get().lower()
            if value == '':
                data = source_data_or_callable() if callable(source_data_or_callable) else source_data_or_callable
                combo['values'] = data
            else:
                data = source_data_or_callable() if callable(source_data_or_callable) else source_data_or_callable
                filtered_data = [item for item in data if value in item.lower()]
                combo['values'] = filtered_data[:50]
                
        combo.bind('<KeyRelease>', on_keyrelease)

    def get_conceptos_validos(self):
        """Retorna conceptos filtrados por el grupo seleccionado."""
        grupo_val = self.grupo_combo.get()
        if not grupo_val:
            return [f"{c[0]}: {c[1]}" for c in self.conceptos_completos]
        
        try:
            gid_sel = int(grupo_val.split(':')[0])
            return [f"{c[0]}: {c[1]}" for c in self.conceptos_completos if c[2] == gid_sel]
        except:
            return []

    def on_grupo_seleccionado(self, event):
        """Al seleccionar un grupo, filtra los conceptos."""
        self.concepto_combo.set('')
        vals = self.get_conceptos_validos()
        self.concepto_combo['values'] = vals

    def guardar_movimiento(self):
        """Guarda el movimiento en la base de datos."""
        # Recolección y validación
        try:
            fecha = self.date_entry.get_date()
            cuenta_txt = self.cuenta_combo.get()
            valor_txt = self.valor_entry.get()
            moneda_txt = self.moneda_combo.get()
            
            # Validación básica
            if not cuenta_txt or not valor_txt or not moneda_txt:
                messagebox.showwarning("Faltan Datos", "Fecha, Cuenta, Valor y Moneda son obligatorios.")
                return
            
            cuenta_id = int(cuenta_txt.split(':')[0])
            moneda_id = int(moneda_txt.split(':')[0])
            valor = float(valor_txt.replace(',', ''))
            
            # Datos opcionales y lógica de negocio
            # Descripción y Referencia: Se guardan vacíos según requerimiento
            desc = "" 
            ref = ""
            
            detalle = self.detalle_entry.get().strip()
            
            tercero_txt = self.tercero_combo.get()
            tercero_id = int(tercero_txt.split(':')[0]) if tercero_txt and ':' in tercero_txt else None
            
            grupo_txt = self.grupo_combo.get()
            grupo_id = int(grupo_txt.split(':')[0]) if grupo_txt and ':' in grupo_txt else None
            
            concepto_txt = self.concepto_combo.get()
            concepto_id = int(concepto_txt.split(':')[0]) if concepto_txt and ':' in concepto_txt else None
            
            # Insertar
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            sql = """
                INSERT INTO movimientos 
                (Fecha, Descripcion, Referencia, Valor, MonedaID, CuentaID, TerceroID, GrupoID, ConceptoID, Detalle, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING Id;
            """
            
            cursor.execute(sql, (fecha, desc, ref, valor, moneda_id, cuenta_id, tercero_id, grupo_id, concepto_id, detalle))
            new_id = cursor.fetchone()[0]
            conn.commit()
            
            self.agregar_log(f"✓ Movimiento guardado exitosamente. ID: {new_id}", 'success')
            
            self.limpiar_formulario()
            
            cursor.close()
            conn.close()
            
        except ValueError:
            messagebox.showerror("Error de Formato", "El valor debe ser numérico.")
        except Exception as e:
            self.agregar_log(f"Error al guardar: {e}", 'error')
            messagebox.showerror("Error", f"Ocurrió un error al guardar: {e}")

    def limpiar_formulario(self):
        """Limpia los campos del formulario para un nuevo ingreso."""
        self.valor_entry.delete(0, tk.END)
        self.detalle_entry.delete(0, tk.END)
        
        self.tercero_combo.set('')
        self.grupo_combo.set('')
        self.concepto_combo.set('')
        
        self.valor_entry.focus()

    def agregar_log(self, mensaje, tipo='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {mensaje}\n", tipo)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = IngresarMovimientosGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Error fatal: {e}")
