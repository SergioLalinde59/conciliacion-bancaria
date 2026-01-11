#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz de Gestión CRUD para Tabla Terceros
Permite crear, leer, actualizar y eliminar registros de terceros.

Nota: Después de 3NF, los campos 'descripcion' y 'referencia' ahora están
en la tabla tercero_descripciones. Este CRUD solo gestiona la tabla maestra terceros.

Autor: Antigravity
Fecha: 2025-12-29
Actualizado: 2026-01-07 - Adaptado a esquema normalizado 3NF
"""

import psycopg2
from psycopg2 import IntegrityError
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Configuración de BD
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}


class GestionarTercerosGUI:
    """Interfaz gráfica para gestionar terceros."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Terceros")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Variables
        self.conn = None
        self.cursor = None
        self.registros = []
        self.registros_filtrados = []
        self.orden_ascendente = {}
        
        self.setup_ui()
        self.cargar_datos()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Gestión de Terceros", 
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0,  pady=(0, 15))
        
        # Frame de búsqueda
        search_frame = ttk.LabelFrame(main_frame, text="Búsqueda", padding="10")
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Filtrar:").grid(row=0, column=0, sticky=tk.W)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filtrar_datos())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10)
        
        ttk.Button(search_frame, text="Limpiar", 
                  command=lambda: self.search_var.set("")).grid(row=0, column=2)
        
        # Frame del DataGrid
        grid_frame = ttk.LabelFrame(main_frame, text="Registros", padding="5")
        grid_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.rowconfigure(0, weight=1)
        
        # TreeView - Solo ID, Tercero (3NF: sin descripcion/referencia)
        columns = ("ID", "Tercero", "Activa")
        self.tree = ttk.Treeview(grid_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("ID", text="ID", command=lambda: self.ordenar_por_columna("ID"))
        self.tree.heading("Tercero", text="Tercero", command=lambda: self.ordenar_por_columna("Tercero"))
        self.tree.heading("Activa", text="Activa", command=lambda: self.ordenar_por_columna("Activa"))
        
        self.tree.column("ID", width=60, anchor=tk.CENTER)
        self.tree.column("Tercero", width=400, anchor=tk.W)
        self.tree.column("Activa", width=80, anchor=tk.CENTER)
        
        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Nota informativa
        note_frame = ttk.Frame(main_frame)
        note_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Label(note_frame, 
                  text="ℹ️ Los alias (descripción/referencia) se gestionan en 'Alias Terceros'",
                  font=("Arial", 9, "italic"), foreground="gray").pack()
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, pady=10)
        
        ttk.Button(button_frame, text="➕ Nuevo Tercero", 
                  command=self.nuevo_registro, width=20).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="✏️ Editar", 
                  command=self.editar_registro, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="🗑️ Eliminar", 
                  command=self.eliminar_registro, width=20).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="🔄 Actualizar", 
                  command=self.cargar_datos, width=20).grid(row=0, column=3, padx=5)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(status_frame, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.count_label = ttk.Label(status_frame, text="Total: 0", relief=tk.SUNKEN, anchor=tk.E)
        self.count_label.pack(side=tk.RIGHT)
        
    def conectar(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar:\n{e}")
            return False
            
    def desconectar(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:  
            self.conn.close()
            
    def cargar_datos(self):
        if not self.conectar():
            return
            
        try:
            # Solo columnas existentes: terceroid, tercero, activa
            self.cursor.execute("SELECT terceroid, tercero, activa FROM terceros ORDER BY terceroid")
            self.registros = self.cursor.fetchall()
            self.registros_filtrados = self.registros.copy()
            self.actualizar_tree()
            self.status_label.config(text=f"✓ Datos cargados - {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos:\n{e}")
            self.status_label.config(text="✗ Error al cargar")
        finally:
            self.desconectar()
            
    def actualizar_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for reg in self.registros_filtrados:
            reg_display = (
                reg[0],  # terceroid
                reg[1] if reg[1] is not None else "",  # tercero
                "Sí" if reg[2] else "No"  # activa
            )
            self.tree.insert("", tk.END, values=reg_display)
            
        total = len(self.registros)
        mostrados = len(self.registros_filtrados)
        if total == mostrados:
            self.count_label.config(text=f"Total: {total}")
        else:
            self.count_label.config(text=f"Mostrando: {mostrados} de {total}")
            
    def filtrar_datos(self):
        termino = self.search_var.get().lower()
        
        if not termino:
            self.registros_filtrados = self.registros.copy()
        else:
            self.registros_filtrados = [
                reg for reg in self.registros
                if any(termino in str(campo).lower() for campo in reg)
            ]
            
        self.actualizar_tree()
        
    def ordenar_por_columna(self, columna):
        col_index = {"ID": 0, "Tercero": 1, "Activa": 2}[columna]
        ascending = self.orden_ascendente.get(columna, True)
        self.orden_ascendente[columna] = not ascending
        self.registros_filtrados.sort(key=lambda x: x[col_index] if x[col_index] else "", reverse=not ascending)
        self.actualizar_tree()
        
    def on_double_click(self, event):
        self.editar_registro()
        
    def nuevo_registro(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Nuevo Tercero")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Nombre del Tercero:").grid(row=0, column=0, sticky=tk.W, pady=5)
        tercero_var = tk.StringVar()
        tercero_entry = ttk.Entry(frame, textvariable=tercero_var, width=40)
        tercero_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        tercero_entry.focus()
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=20)
        
        def guardar():
            tercero = tercero_var.get().strip()
            
            if not tercero:
                messagebox.showwarning("Validación", "El campo 'Tercero' es obligatorio.")
                return
                
            if not self.conectar():
                return
                
            try:
                self.cursor.execute(
                    "INSERT INTO terceros (tercero) VALUES (%s)",
                    (tercero,)
                )
                self.conn.commit()
                messagebox.showinfo("Éxito", "Tercero creado exitosamente.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror(
                        "Error de Duplicado",
                        f"Ya existe un tercero con el nombre:\n\n"
                        f"  \"{tercero}\"\n\n"
                        "El nombre del tercero debe ser único."
                    )
                else:
                    messagebox.showerror("Error", f"Error de integridad:\n{e}")
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Error al crear:\n{e}")
            finally:
                self.desconectar()
                
        ttk.Button(button_frame, text="Guardar", command=guardar, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
    def editar_registro(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona un registro para editar.")
            return
            
        item = self.tree.item(selected[0])
        valores = item['values']
        terceroid, tercero_actual, activa_str = valores
        
        tercero_actual = tercero_actual if tercero_actual else ""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Tercero")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Nombre del Tercero:").grid(row=0, column=0, sticky=tk.W, pady=5)
        tercero_var = tk.StringVar(value=tercero_actual)
        ttk.Entry(frame, textvariable=tercero_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=20)
        
        def guardar():
            tercero = tercero_var.get().strip()
            
            if not tercero:
                messagebox.showwarning("Validación", "El campo 'Tercero' es obligatorio.")
                return
                
            if not self.conectar():
                return
                
            try:
                self.cursor.execute(
                    "UPDATE terceros SET tercero = %s WHERE terceroid = %s",
                    (tercero, terceroid)
                )
                self.conn.commit()
                messagebox.showinfo("Éxito", "Tercero actualizado exitosamente.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror(
                        "Error de Duplicado",
                        f"Ya existe un tercero con el nombre:\n\n"
                        f"  \"{tercero}\"\n\n"
                        "El nombre del tercero debe ser único."
                    )
                else:
                    messagebox.showerror("Error", f"Error de integridad:\n{e}")
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Error:\n{e}")
            finally:
                self.desconectar()
                
        ttk.Button(button_frame, text="Guardar", command=guardar, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
    def eliminar_registro(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona un registro para eliminar.")
            return
            
        item = self.tree.item(selected[0])
        valores = item['values']
        terceroid, tercero, activa = valores
        
        count = self.validar_integridad(terceroid)
        
        if count > 0:
            messagebox.showerror(
                "⚠️ Registro en Uso",
                f"⚠️ Este registro está siendo usado en {count} movimiento(s).\n\n"
                f"  Tercero: \"{tercero}\"\n\n"
                "No se puede eliminar. Primero elimina/modifica los movimientos relacionados."
            )
            return
            
        respuesta = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Eliminar este tercero?\n\n"
            f"  Tercero: \"{tercero}\"\n\n"
            "Esta acción no se puede deshacer.",
            icon='question'
        )
        
        if not respuesta:
            return
            
        if not self.conectar():
            return
            
        try:
            self.cursor.execute("DELETE FROM terceros WHERE terceroid = %s", (terceroid,))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Tercero eliminado exitosamente.")
            self.cargar_datos()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Error al eliminar:\n{e}")
        finally:
            self.desconectar()
            
    def validar_integridad(self, terceroid):
        if not self.conectar():
            return 0
            
        try:
            self.cursor.execute("SELECT COUNT(*) FROM movimientos WHERE TerceroID = %s", (terceroid,))
            count = self.cursor.fetchone()[0]
            return count
        except:
            return 0
        finally:
            self.desconectar()


def main():
    root = tk.Tk()
    app = GestionarTercerosGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
