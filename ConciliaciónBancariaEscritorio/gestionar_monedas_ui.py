#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz de Gestión CRUD para Tabla Monedas
Permite crear, leer, actualizar y eliminar registros de monedas.

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


class GestionarMonedasGUI:
    """Interfaz gráfica para gestionar monedas."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Monedas")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.conn = None
        self.cursor = None
        self.registros = []
        self.registros_filtrados = []
        self.orden_ascendente = {}
        
        self.setup_ui()
        self.cargar_datos()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        ttk.Label(main_frame, text="Gestión de Monedas", 
                 font=("Arial", 16, "bold")).grid(row=0, column=0, pady=(0, 15))
        
        # Búsqueda
        search_frame = ttk.LabelFrame(main_frame, text="Búsqueda", padding="10")
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Filtrar:").grid(row=0, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filtrar_datos())
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10)
        ttk.Button(search_frame, text="Limpiar", command=lambda: self.search_var.set("")).grid(row=0, column=2)
        
        # DataGrid
        grid_frame = ttk.LabelFrame(main_frame, text="Registros", padding="5")
        grid_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.rowconfigure(0, weight=1)
        
        columns = ("ID", "ISO Code", "Moneda")
        self.tree = ttk.Treeview(grid_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("ID", text="ID", command=lambda: self.ordenar_por_columna("ID"))
        self.tree.heading("ISO Code", text="ISO Code", command=lambda: self.ordenar_por_columna("ISO Code"))
        self.tree.heading("Moneda", text="Moneda", command=lambda: self.ordenar_por_columna("Moneda"))
        
        self.tree.column("ID", width=80, anchor=tk.CENTER)
        self.tree.column("ISO Code", width=120, anchor=tk.CENTER)
        self.tree.column("Moneda", width=400, anchor=tk.W)
        
        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.tree.bind("<Double-1>", lambda e: self.editar_registro())
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(button_frame, text="➕ Nueva Moneda", command=self.nuevo_registro, width=20).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="✏️ Editar", command=self.editar_registro, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="🗑️ Eliminar", command=self.eliminar_registro, width=20).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="🔄 Actualizar", command=self.cargar_datos, width=20).grid(row=0, column=3, padx=5)
        
        # Status
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
            self.cursor.execute("SELECT monedaid, isocode, moneda FROM monedas ORDER BY monedaid")
            self.registros = self.cursor.fetchall()
            self.registros_filtrados = self.registros.copy()
            self.actualizar_tree()
            self.status_label.config(text=f"✓ Datos cargados - {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar:\n{e}")
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
        col_index = {"ID": 0, "ISO Code": 1, "Moneda": 2}[columna]
        ascending = self.orden_ascendente.get(columna, True)
        self.orden_ascendente[columna] = not ascending
        self.registros_filtrados.sort(key=lambda x: x[col_index], reverse=not ascending)
        self.actualizar_tree()
        
    def nuevo_registro(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Nueva Moneda")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 90
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Código ISO:").grid(row=0, column=0, sticky=tk.W, pady=5)
        isocode_var = tk.StringVar()
        isocode_entry = ttk.Entry(frame, textvariable=isocode_var, width=40)
        isocode_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        isocode_entry.focus()
        
        ttk.Label(frame, text="Moneda:").grid(row=1, column=0, sticky=tk.W, pady=5)
        moneda_var = tk.StringVar()
        ttk.Entry(frame, textvariable=moneda_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def guardar():
            isocode = isocode_var.get().strip()
            moneda = moneda_var.get().strip()
            
            if not isocode or not moneda:
                messagebox.showwarning("Validación", "Todos los campos son obligatorios.")
                return
                
            if not self.conectar():
                return
                
            try:
                self.cursor.execute("INSERT INTO monedas (isocode, moneda) VALUES (%s, %s)", (isocode, moneda))
                self.conn.commit()
                messagebox.showinfo("Éxito", "Moneda creada exitosamente.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror("Error de Duplicado",
                        f"Ya existe una moneda:\n\n  \"{moneda}\"\n\nIngrese un valor diferente.")
                else:
                    messagebox.showerror("Error", f"Error de integridad:\n{e}")
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
        monedaid, isocode_actual, moneda_actual = valores
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Moneda")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 90
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Código ISO:").grid(row=0, column=0, sticky=tk.W, pady=5)
        isocode_var = tk.StringVar(value=isocode_actual)
        ttk.Entry(frame, textvariable=isocode_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Moneda:").grid(row=1, column=0, sticky=tk.W, pady=5)
        moneda_var = tk.StringVar(value=moneda_actual)
        ttk.Entry(frame, textvariable=moneda_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def guardar():
            isocode = isocode_var.get().strip()
            moneda = moneda_var.get().strip()
            
            if not isocode or not moneda:
                messagebox.showwarning("Validación", "Todos los campos son obligatorios.")
                return
                
            if not self.conectar():
                return
                
            try:
                self.cursor.execute("UPDATE monedas SET isocode = %s, moneda = %s WHERE monedaid = %s", 
                                  (isocode, moneda, monedaid))
                self.conn.commit()
                messagebox.showinfo("Éxito", "Moneda actualizada.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror("Error de Duplicado",
                        f"Ya existe: \"{moneda}\"\n\nIngrese un valor diferente.")
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
        monedaid, isocode, moneda = valores
        
        count = self.validar_integridad(monedaid)
        if count > 0:
            messagebox.showerror("⚠️ Registro en Uso",
                f"Este registro está en {count} movimiento(s).\n\n  Moneda: \"{moneda}\"\n\n"
                "No se puede eliminar.")
            return
            
        if not messagebox.askyesno("Confirmar", f"¿Eliminar?\n\n  Moneda: \"{moneda}\""):
            return
            
        if not self.conectar():
            return
            
        try:
            self.cursor.execute("DELETE FROM monedas WHERE monedaid = %s", (monedaid,))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Eliminada.")
            self.cargar_datos()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Error:\n{e}")
        finally:
            self.desconectar()
            
    def validar_integridad(self, monedaid):
        if not self.conectar():
            return 0
        try:
            self.cursor.execute("SELECT COUNT(*) FROM movimientos WHERE MonedaID = %s", (monedaid,))
            return self.cursor.fetchone()[0]
        except:
            return 0
        finally:
            self.desconectar()


def main():
    root = tk.Tk()
    app = GestionarMonedasGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
