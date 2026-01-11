#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz de Gestión CRUD para Tabla Tipo de Movimiento
Permite crear, leer, actualizar y eliminar tipos de movimiento.

Autor: Antigravity
Fecha: 2025-12-29
"""

import psycopg2
from psycopg2 import IntegrityError
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'user': 'postgres',
    'password': 'SLB',
    'database': 'Mvtos'
}


class GestionarTipoMovGUI:
    """Interfaz gráfica para gestionar tipos de movimiento."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Tipos de Movimiento")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        self.conn = None
        self.cursor = None
        self.registros = []
        self.registros_filtrados = []
        self.orden_ascendente = {}
        
        self.setup_ui()
        self.cargar_datos()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        ttk.Label(main_frame, text="Gestión de Tipos de Movimiento", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, pady=(0, 15))
        
        search_frame = ttk.LabelFrame(main_frame, text="Búsqueda", padding="10")
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Filtrar:").grid(row=0, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filtrar_datos())
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10)
        ttk.Button(search_frame, text="Limpiar", command=lambda: self.search_var.set("")).grid(row=0, column=2)
        
        grid_frame = ttk.LabelFrame(main_frame, text="Registros", padding="5")
        grid_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.rowconfigure(0, weight=1)
        
        columns = ("ID", "Tipo de Movimiento")
        self.tree = ttk.Treeview(grid_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("ID", text="ID", command=lambda: self.ordenar_por_columna("ID"))
        self.tree.heading("Tipo de Movimiento", text="Tipo de Movimiento", command=lambda: self.ordenar_por_columna("Tipo de Movimiento"))
        
        self.tree.column("ID", width=80, anchor=tk.CENTER)
        self.tree.column("Tipo de Movimiento", width=400, anchor=tk.W)
        
        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.tree.bind("<Double-1>", lambda e: self.editar_registro())
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(button_frame, text="➕ Nuevo Tipo", command=self.nuevo_registro, width=20).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="✏️ Editar", command=self.editar_registro, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="🗑️ Eliminar", command=self.eliminar_registro, width=20).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="🔄 Actualizar", command=self.cargar_datos, width=20).grid(row=0, column=3, padx=5)
        
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
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
            messagebox.showerror("Error", f"No se pudo conectar:\n{e}")
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
            self.cursor.execute("SELECT tipomovid, tipomov FROM tipomov ORDER BY tipomovid")
            self.registros = self.cursor.fetchall()
            self.registros_filtrados = self.registros.copy()
            self.actualizar_tree()
            self.status_label.config(text=f"✓ Datos cargados - {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Error:\n{e}")
        finally:
            self.desconectar()
            
    def actualizar_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for reg in self.registros_filtrados:
            self.tree.insert("", tk.END, values=reg)
        total = len(self.registros)
        mostrados = len(self.registros_filtrados)
        self.count_label.config(text=f"Total: {total}" if total == mostrados else f"Mostrando: {mostrados} de {total}")
            
    def filtrar_datos(self):
        termino = self.search_var.get().lower()
        self.registros_filtrados = self.registros.copy() if not termino else [
            reg for reg in self.registros if any(termino in str(campo).lower() for campo in reg)
        ]
        self.actualizar_tree()
        
    def ordenar_por_columna(self, columna):
        col_index = {"ID": 0, "Tipo de Movimiento": 1}[columna]
        ascending = self.orden_ascendente.get(columna, True)
        self.orden_ascendente[columna] = not ascending
        self.registros_filtrados.sort(key=lambda x: x[col_index], reverse=not ascending)
        self.actualizar_tree()
        
    def nuevo_registro(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Nuevo Tipo de Movimiento")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 75
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Tipo de Movimiento:").grid(row=0, column=0, sticky=tk.W, pady=5)
        tipomov_var = tk.StringVar()
        tipomov_entry = ttk.Entry(frame, textvariable=tipomov_var, width=40)
        tipomov_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        tipomov_entry.focus()
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=20)
        
        def guardar():
            tipomov = tipomov_var.get().strip()
            
            if not tipomov:
                messagebox.showwarning("Validación", "El campo es obligatorio.")
                return
                
            if not self.conectar():
                return
                
            try:
                self.cursor.execute("INSERT INTO tipomov (tipomov) VALUES (%s)", (tipomov,))
                self.conn.commit()
                messagebox.showinfo("Éxito", "Tipo creado exitosamente.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror("Error de Duplicado", f"Ya existe: \"{tipomov}\"")
                else:
                    messagebox.showerror("Error", f"Error:\n{e}")
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Error:\n{e}")
            finally:
                self.desconectar()
                
        ttk.Button(button_frame, text="Guardar", command=guardar, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
    def editar_registro(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona un registro.")
            return
            
        valores = self.tree.item(selected[0])['values']
        tipomovid, tipomov_actual = valores
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Tipo de Movimiento")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 75
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Tipo de Movimiento:").grid(row=0, column=0, sticky=tk.W, pady=5)
        tipomov_var = tk.StringVar(value=tipomov_actual)
        ttk.Entry(frame, textvariable=tipomov_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=20)
        
        def guardar():
            tipomov = tipomov_var.get().strip()
            
            if not tipomov:
                messagebox.showwarning("Validación", "El campo es obligatorio.")
                return
                
            if not self.conectar():
                return
                
            try:
                self.cursor.execute("UPDATE tipomov SET tipomov = %s WHERE tipomovid = %s", (tipomov, tipomovid))
                self.conn.commit()
                messagebox.showinfo("Éxito", "Actualizado.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror("Error de Duplicado", f"Ya existe: \"{tipomov}\"")
                else:
                    messagebox.showerror("Error", f"Error:\n{e}")
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
            messagebox.showwarning("Advertencia", "Selecciona un registro.")
            return
            
        valores = self.tree.item(selected[0])['values']
        tipomovid, tipomov = valores
        
        # Nota: tipomov no tiene FK directo en movimientos, pero validamos por si acaso
        if not messagebox.askyesno("Confirmar", f"¿Eliminar?\n\n  Tipo: \"{tipomov}\""):
            return
            
        if not self.conectar():
            return
            
        try:
            self.cursor.execute("DELETE FROM tipomov WHERE tipomovid = %s", (tipomovid,))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Eliminado.")
            self.cargar_datos()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Error:\n{e}")
        finally:
            self.desconectar()


def main():
    root = tk.Tk()
    app = GestionarTipoMovGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
