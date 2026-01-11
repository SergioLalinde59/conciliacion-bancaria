#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reglas de Negocio para Asignación Automática de TerceroID - Interfaz Gráfica
Permite visualizar y aprobar asignaciones automáticas basadas en reglas de negocio

Autor: Antigravity
Fecha: 2025-12-29
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import psycopg2
from datetime import datetime
import threading

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}


class ReglasAsignacionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Asignación Automática de Terceros por Reglas de Negocio")
        self.root.geometry("1200x850")
        self.root.resizable(True, True)
        
        # Variables
        self.conn = None
        self.asignaciones_sugeridas = []
        self.movimientos_sin_contacto = []
        self.is_processing = False
        self.asignaciones_aprobadas = []
        
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
        # Log inicial
        self.agregar_log("✓ Aplicación iniciada correctamente", 'success')
        self.agregar_log("🔍 Presiona 'Analizar' para buscar asignaciones automáticas", 'info')
    
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)  # Lista de asignaciones
        main_frame.rowconfigure(5, weight=1)  # Log
        
        # Título
        title_label = ttk.Label(main_frame, text="Asignación Automática de Terceros", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # === SECCIÓN 1: Reglas Aplicadas ===
        rules_frame = ttk.LabelFrame(main_frame, text="1. Reglas de Negocio Aplicadas", padding="10")
        rules_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        rules_text = """
📋 Regla 1: Coincidencia por Referencia
   → Si un movimiento tiene una referencia que coincide con movimientos ya asignados,
     se sugiere asignar el mismo tercero.
     
💡 Al presionar 'Analizar', el sistema buscará automáticamente estas coincidencias.
        """
        
        ttk.Label(rules_frame, text=rules_text, font=('Arial', 9), 
                 foreground='gray', justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)
        
        # === SECCIÓN 2: Estadísticas ===
        stats_frame = ttk.LabelFrame(main_frame, text="2. Estadísticas", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Container para las tres cajas de estadísticas
        stats_container = ttk.Frame(stats_frame)
        stats_container.grid(row=0, column=0, pady=5)
        
        # Caja 1: Sin Contacto
        box1 = ttk.Frame(stats_container, relief='solid', borderwidth=2)
        box1.grid(row=0, column=0, padx=10)
        ttk.Label(box1, text="❌ Sin TerceroID", font=('Arial', 9, 'bold')).pack(pady=(5, 0))
        self.stats_sin_contacto = ttk.Label(box1, text="0", font=('Arial', 20, 'bold'), foreground='red')
        self.stats_sin_contacto.pack(pady=(0, 5), padx=20)
        
        # Caja 2: Asignaciones Sugeridas
        box2 = ttk.Frame(stats_container, relief='solid', borderwidth=2)
        box2.grid(row=0, column=1, padx=10)
        ttk.Label(box2, text="💡 Sugerencias", font=('Arial', 9, 'bold')).pack(pady=(5, 0))
        self.stats_sugerencias = ttk.Label(box2, text="0", font=('Arial', 20, 'bold'), foreground='orange')
        self.stats_sugerencias.pack(pady=(0, 5), padx=20)
        
        # Caja 3: A Aplicar
        box3 = ttk.Frame(stats_container, relief='solid', borderwidth=2)
        box3.grid(row=0, column=2, padx=10)
        ttk.Label(box3, text="✓ A Aplicar", font=('Arial', 9, 'bold')).pack(pady=(5, 0))
        self.stats_a_aplicar = ttk.Label(box3, text="0", font=('Arial', 20, 'bold'), foreground='green')
        self.stats_a_aplicar.pack(pady=(0, 5), padx=20)
        
        # === SECCIÓN 3: Lista de Asignaciones Sugeridas ===
        list_frame = ttk.LabelFrame(main_frame, text="3. Asignaciones Sugeridas", padding="10")
        list_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # TreeView para mostrar asignaciones
        columns = ('sel', 'id', 'fecha', 'descripcion', 'referencia', 'valor', 'contacto', 'veces')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        self.tree.heading('sel', text='✓')
        self.tree.heading('id', text='ID Mvto')
        self.tree.heading('fecha', text='Fecha')
        self.tree.heading('descripcion', text='Descripción')
        self.tree.heading('referencia', text='Referencia')
        self.tree.heading('valor', text='Valor')
        self.tree.heading('contacto', text='Tercero Sugerido')
        self.tree.heading('veces', text='# Usos')
        
        self.tree.column('sel', width=30, anchor='center')
        self.tree.column('id', width=70, anchor='center')
        self.tree.column('fecha', width=90)
        self.tree.column('descripcion', width=250)
        self.tree.column('referencia', width=120)
        self.tree.column('valor', width=110, anchor='e')
        self.tree.column('contacto', width=200)
        self.tree.column('veces', width=60, anchor='center')
        
        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Binding para toggle de selección al hacer clic
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # Botones de selección rápida
        select_frame = ttk.Frame(list_frame)
        select_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(select_frame, text="Seleccionar Todas", 
                  command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="Deseleccionar Todas", 
                  command=self.deselect_all).pack(side=tk.LEFT, padx=5)
        
        # === SECCIÓN 4: Acciones ===
        action_frame = ttk.LabelFrame(main_frame, text="4. Acciones", padding="10")
        action_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        action_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(action_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Botones de acción
        button_container = ttk.Frame(action_frame)
        button_container.grid(row=1, column=0)
        
        self.analyze_button = ttk.Button(button_container, text="🔍 Analizar Movimientos", 
                                        command=self.analizar_movimientos, width=25)
        self.analyze_button.grid(row=0, column=0, padx=5)
        
        self.apply_button = ttk.Button(button_container, text="✓ Aplicar Seleccionadas", 
                                       command=self.aplicar_asignaciones, state='disabled', width=25)
        self.apply_button.grid(row=0, column=1, padx=5)
        
        self.clear_button = ttk.Button(button_container, text="🗑️ Limpiar", 
                                      command=self.limpiar_todo, width=20)
        self.clear_button.grid(row=0, column=2, padx=5)
        
        # === SECCIÓN 5: Log de Eventos ===
        log_frame = ttk.LabelFrame(main_frame, text="Log de Eventos", padding="10")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Área de texto con scroll para el log
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80, 
                                                   font=('Courier', 9), state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar colores para el log
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
    
    def conectar(self):
        """Conecta a la base de datos"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            self.agregar_log(f"✗ Error al conectar a la base de datos: {e}", 'error')
            return False
    
    def desconectar(self):
        """Cierra la conexión"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def analizar_movimientos(self):
        """Inicia el análisis de movimientos para encontrar sugerencias."""
        if self.is_processing:
            messagebox.showwarning("Advertencia", "Ya hay un proceso en ejecución.")
            return
        
        self.agregar_log("=" * 70, 'info')
        self.agregar_log("🔍 Iniciando análisis de movimientos...", 'info')
        self.analyze_button.config(state='disabled')
        self.is_processing = True
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=self._ejecutar_analisis)
        thread.daemon = True
        thread.start()
    
    def _ejecutar_analisis(self):
        """Ejecuta el análisis en background."""
        try:
            if not self.conectar():
                return
            
            cursor = self.conn.cursor()
            
            # PASO 1: Contar movimientos sin contacto
            self.agregar_log("📋 Paso 1: Contando movimientos sin TerceroID...", 'info')
            
            query_count = """
            SELECT COUNT(*) 
            FROM movimientos
            WHERE TerceroID IS NULL
            """
            cursor.execute(query_count)
            count_sin_contacto = cursor.fetchone()[0]
            
            self.stats_sin_contacto.config(text=str(count_sin_contacto))
            self.agregar_log(f"✓ {count_sin_contacto} movimientos sin TerceroID", 'info')
            
            if count_sin_contacto == 0:
                self.agregar_log("🎉 ¡Todos los movimientos ya tienen TerceroID asignado!", 'success')
                cursor.close()
                self.desconectar()
                self.is_processing = False
                self.analyze_button.config(state='normal')
                return
            
            # PASO 2: Buscar asignaciones sugeridas
            self.agregar_log("🔍 Paso 2: Buscando coincidencias por referencia...", 'info')
            
            query_asignaciones = """
            SELECT DISTINCT
                m1.Id as movimiento_sin_contacto_id,
                m1.Descripcion as descripcion_movimiento,
                m1.Referencia as referencia,
                m1.Valor as valor,
                m1.Fecha as fecha,
                m2.TerceroID as terceroid_sugerido,
                c.tercero as nombre_tercero,
                c.descripcion as descripcion_tercero,
                COUNT(*) OVER (PARTITION BY m1.Referencia) as veces_referencia_usado
            FROM movimientos m1
            INNER JOIN movimientos m2 
                ON m1.Referencia = m2.Referencia 
                AND m1.Referencia IS NOT NULL 
                AND m1.Referencia != ''
            INNER JOIN terceros c 
                ON m2.TerceroID = c.terceroid
            WHERE 
                m1.TerceroID IS NULL 
                AND m2.TerceroID IS NOT NULL
            ORDER BY m1.Fecha DESC, m1.Id
            """
            
            cursor.execute(query_asignaciones)
            self.asignaciones_sugeridas = cursor.fetchall()
            
            cursor.close()
            self.desconectar()
            
            # Mostrar resultados
            if self.asignaciones_sugeridas:
                self.agregar_log(f"✓ Se encontraron {len(self.asignaciones_sugeridas)} asignaciones sugeridas", 'success')
                self.mostrar_asignaciones()
                self.apply_button.config(state='normal')
            else:
                self.agregar_log("⚠️ No se encontraron coincidencias de referencias", 'warning')
                self.agregar_log("   Necesitas asignar algunos terceros manualmente primero", 'info')
            
            self.stats_sugerencias.config(text=str(len(self.asignaciones_sugeridas)))
            
        except Exception as e:
            self.agregar_log(f"✗ Error durante el análisis: {e}", 'error')
            import traceback
            traceback.print_exc()
        finally:
            self.is_processing = False
            self.analyze_button.config(state='normal')
    
    def mostrar_asignaciones(self):
        """Muestra las asignaciones sugeridas en el TreeView."""
        # Limpiar tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Agrupar por contacto para mejor visualización
        for asig in self.asignaciones_sugeridas:
            mov_id = asig[0]
            descripcion = asig[1]
            referencia = asig[2]
            valor = asig[3]
            fecha = asig[4]
            contactoid = asig[5]
            nombre_contacto = asig[6]
            veces_usado = asig[8]
            
            # Insertar con checkmark predeterminado
            self.tree.insert('', 'end', values=(
                '☑',  # Seleccionado por defecto
                mov_id,
                fecha.strftime('%Y-%m-%d'),
                descripcion[:40],
                referencia,
                f"${valor:,.2f}",
                nombre_contacto,
                veces_usado
            ), tags=('selected',))
        
        # Configurar tag visual para seleccionados
        self.tree.tag_configure('selected', background='#e6ffe6')
        self.tree.tag_configure('unselected', background='white')
        
        # Actualizar contador de seleccionadas
        self.actualizar_contador_seleccionadas()
        
        self.agregar_log("📊 Asignaciones mostradas en la tabla (todas seleccionadas por defecto)", 'info')
    
    def on_tree_click(self, event):
        """Maneja el clic en el tree para toggle de selección."""
        region = self.tree.identify('region', event.x, event.y)
        if region == 'cell':
            item = self.tree.identify_row(event.y)
            if item:
                # Toggle selection
                current_tags = self.tree.item(item, 'tags')
                if 'selected' in current_tags:
                    self.tree.item(item, tags=('unselected',), values=(
                        '☐', *self.tree.item(item, 'values')[1:]
                    ))
                else:
                    self.tree.item(item, tags=('selected',), values=(
                        '☑', *self.tree.item(item, 'values')[1:]
                    ))
                
                self.actualizar_contador_seleccionadas()
    
    def select_all(self):
        """Selecciona todas las asignaciones."""
        for item in self.tree.get_children():
            self.tree.item(item, tags=('selected',), values=(
                '☑', *self.tree.item(item, 'values')[1:]
            ))
        self.actualizar_contador_seleccionadas()
        self.agregar_log("✓ Todas las asignaciones seleccionadas", 'info')
    
    def deselect_all(self):
        """Deselecciona todas las asignaciones."""
        for item in self.tree.get_children():
            self.tree.item(item, tags=('unselected',), values=(
                '☐', *self.tree.item(item, 'values')[1:]
            ))
        self.actualizar_contador_seleccionadas()
        self.agregar_log("⚠️ Todas las asignaciones deseleccionadas", 'warning')
    
    def actualizar_contador_seleccionadas(self):
        """Actualiza el contador de asignaciones seleccionadas."""
        count = sum(1 for item in self.tree.get_children() 
                   if 'selected' in self.tree.item(item, 'tags'))
        self.stats_a_aplicar.config(text=str(count))
    
    def aplicar_asignaciones(self):
        """Aplica las asignaciones seleccionadas."""
        # Obtener IDs de movimientos seleccionados
        seleccionados = []
        for item in self.tree.get_children():
            if 'selected' in self.tree.item(item, 'tags'):
                values = self.tree.item(item, 'values')
                mov_id = values[1]
                # Buscar la asignación completa
                for asig in self.asignaciones_sugeridas:
                    if asig[0] == mov_id:
                        seleccionados.append(asig)
                        break
        
        if not seleccionados:
            messagebox.showwarning("Advertencia", "No hay asignaciones seleccionadas.")
            return
        
        # Confirmar con el usuario
        respuesta = messagebox.askyesno(
            "Confirmar Asignaciones",
            f"¿Estás seguro de aplicar {len(seleccionados)} asignaciones automáticas?\n\n" +
            "Esto actualizará el campo TerceroID en los movimientos seleccionados.",
            icon='question'
        )
        
        if not respuesta:
            self.agregar_log("⚠️ Operación cancelada por el usuario", 'warning')
            return
        
        self.agregar_log("=" * 70, 'info')
        self.agregar_log(f"📤 Aplicando {len(seleccionados)} asignaciones...", 'info')
        self.apply_button.config(state='disabled')
        self.is_processing = True
        
        # Ejecutar en thread separado
        thread = threading.Thread(target=self._ejecutar_aplicacion, args=(seleccionados,))
        thread.daemon = True
        thread.start()
    
    def _ejecutar_aplicacion(self, asignaciones):
        """Ejecuta la aplicación de asignaciones en background."""
        try:
            if not self.conectar():
                return
            
            cursor = self.conn.cursor()
            actualizados = 0
            errores = 0
            
            self.progress_bar['maximum'] = len(asignaciones)
            self.progress_bar['value'] = 0
            
            for i, asig in enumerate(asignaciones, 1):
                movimiento_id = asig[0]
                contactoid = asig[5]
                referencia = asig[2]
                nombre_contacto = asig[6]
                
                try:
                    query = """
                    UPDATE movimientos 
                    SET TerceroID = %s 
                    WHERE Id = %s AND TerceroID IS NULL
                    """
                    
                    cursor.execute(query, (contactoid, movimiento_id))
                    
                    if cursor.rowcount > 0:
                        actualizados += 1
                        if actualizados <= 5:  # Mostrar solo los primeros 5
                            self.agregar_log(
                                f"  ✓ Mvto {movimiento_id} → {nombre_contacto} (ref: {referencia})", 
                                'success'
                            )
                    
                except Exception as e:
                    errores += 1
                    self.agregar_log(f"  ✗ Error en movimiento {movimiento_id}: {e}", 'error')
                    self.conn.rollback()
                    continue
                
                # Actualizar progreso
                self.progress_bar['value'] = i
                if i % 5 == 0 or i == len(asignaciones):
                    self.root.update_idletasks()
            
            # Commit de todos los cambios
            self.conn.commit()
            
            cursor.close()
            self.desconectar()
            
            # Mostrar resultados
            self.agregar_log("=" * 70, 'info')
            if errores == 0:
                self.agregar_log(f"✓✓✓ PROCESO COMPLETADO EXITOSAMENTE ✓✓✓", 'success')
                self.agregar_log(f"✓ {actualizados} movimientos actualizados", 'success')
                messagebox.showinfo("Éxito", 
                                   f"Se actualizaron {actualizados} movimientos exitosamente.")
                
                # Limpiar y reanalizar
                self.limpiar_tabla()
                self.analizar_movimientos()
            else:
                self.agregar_log(f"⚠️ Completado con {errores} errores", 'warning')
                self.agregar_log(f"✓ {actualizados} actualizados, {errores} errores", 'warning')
                messagebox.showwarning("Completado con errores",
                                      f"Se actualizaron {actualizados} movimientos.\n" +
                                      f"{errores} tuvieron errores.")
            
            self.progress_bar['value'] = 0
            
        except Exception as e:
            self.agregar_log(f"✗ Error crítico: {e}", 'error')
            messagebox.showerror("Error", f"Error durante la aplicación:\n{e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_processing = False
            self.apply_button.config(state='normal')
    
    def limpiar_tabla(self):
        """Limpia solo la tabla, manteniendo los datos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.asignaciones_sugeridas = []
        self.stats_sugerencias.config(text="0")
        self.stats_a_aplicar.config(text="0")
        self.apply_button.config(state='disabled')
    
    def limpiar_todo(self):
        """Limpia todos los datos y resetea la interfaz."""
        self.limpiar_tabla()
        
        self.stats_sin_contacto.config(text="0")
        self.progress_bar['value'] = 0
        
        # Limpiar log
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
        
        self.agregar_log("✓ Interfaz limpiada", 'success')
        self.agregar_log("🔍 Presiona 'Analizar' para buscar asignaciones automáticas", 'info')


def main():
    """Función principal."""
    root = tk.Tk()
    app = ReglasAsignacionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
