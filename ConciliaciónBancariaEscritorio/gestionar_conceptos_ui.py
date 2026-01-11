#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz de Gestión CRUD para Tabla Conceptos
Permite crear, leer, actualizar y eliminar conceptos con dropdown para grupos.

Autor: Antigravity
Fecha: 2025-12-29
Actualizado: 2026-01-07 - Removidas columnas claveconcepto y grupo (3NF)
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


class GestionarConceptosGUI:
    """Interfaz gráfica para gestionar conceptos."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Conceptos")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.conn = None
        self.cursor = None
        self.registros = []
        self.registros_filtrados = []
        self.orden_ascendente = {}
        self.grupos_disponibles = []  # Para el dropdown
        
        self.setup_ui()
        self.cargar_datos()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        ttk.Label(main_frame, text="Gestión de Conceptos", 
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
        
        columns = ("ID", "Concepto", "GrupoID_FK", "Grupo")
        self.tree = ttk.Treeview(grid_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("ID", text="ID", command=lambda: self.ordenar_por_columna("ID"))
        self.tree.heading("Concepto", text="Concepto", command=lambda: self.ordenar_por_columna("Concepto"))
        self.tree.heading("GrupoID_FK", text="ID Grupo", command=lambda: self.ordenar_por_columna("GrupoID_FK"))
        self.tree.heading("Grupo", text="Grupo", command=lambda: self.ordenar_por_columna("Grupo"))
        
        self.tree.column("ID", width=60, anchor=tk.CENTER)
        self.tree.column("Concepto", width=350, anchor=tk.W)
        self.tree.column("GrupoID_FK", width=80, anchor=tk.CENTER)
        self.tree.column("Grupo", width=200, anchor=tk.W)
        
        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.tree.bind("<Double-1>", lambda e: self.editar_registro())
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(button_frame, text="➕ Nuevo Concepto", command=self.nuevo_registro, width=20).grid(row=0, column=0, padx=5)
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
            
    def cargar_grupos(self):
        """Carga la lista de grupos disponibles para el dropdown."""
        if not self.conectar():
            return []
        try:
            self.cursor.execute("SELECT grupoid, grupo FROM grupos ORDER BY grupo")
            grupos = self.cursor.fetchall()
            return grupos
        except:
            return []
        finally:
            self.desconectar()
            
    def cargar_datos(self):
        if not self.conectar():
            return
        try:
            self.cursor.execute(
                """SELECT c.conceptoid, c.concepto, c.grupoid_fk, COALESCE(g.grupo, '') as grupo_nombre
                   FROM conceptos c
                   LEFT JOIN grupos g ON c.grupoid_fk = g.grupoid
                   ORDER BY c.conceptoid"""
            )
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
        col_index = {"ID": 0, "Concepto": 1, "GrupoID_FK": 2, "Grupo": 3}[columna]
        ascending = self.orden_ascendente.get(columna, True)
        self.orden_ascendente[columna] = not ascending
        self.registros_filtrados.sort(key=lambda x: x[col_index] if x[col_index] is not None else "", reverse=not ascending)
        self.actualizar_tree()
        
    def nuevo_registro(self):
        # Cargar grupos disponibles
        grupos = self.cargar_grupos()
        if not grupos:
            messagebox.showwarning("Advertencia", "No hay grupos disponibles. Crea grupos primero.")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Nuevo Concepto")
        dialog.geometry("500x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Concepto:").grid(row=0, column=0, sticky=tk.W, pady=5)
        concepto_var = tk.StringVar()
        concepto_entry = ttk.Entry(frame, textvariable=concepto_var, width=45)
        concepto_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        concepto_entry.focus()
        
        ttk.Label(frame, text="Grupo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        grupo_fk_var = tk.StringVar()
        grupo_combo = ttk.Combobox(frame, textvariable=grupo_fk_var, width=43, state="readonly")
        # Crear diccionario de nombre->id y lista de nombres
        grupo_dict = {f"{gid} - {nombre}": gid for gid, nombre in grupos}
        grupo_combo['values'] = list(grupo_dict.keys())
        grupo_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def guardar():
            concepto = concepto_var.get().strip()
            grupo_fk_str = grupo_fk_var.get()
            
            if not concepto:
                messagebox.showwarning("Validación", "El nombre del concepto es obligatorio.")
                return
                
            # Obtener grupoid_fk del dropdown
            grupoid_fk = grupo_dict.get(grupo_fk_str) if grupo_fk_str else None
            
            if not self.conectar():
                return
                
            try:
                self.cursor.execute(
                    "INSERT INTO conceptos (concepto, grupoid_fk) VALUES (%s, %s)",
                    (concepto, grupoid_fk)
                )
                self.conn.commit()
                messagebox.showinfo("Éxito", "Concepto creado exitosamente.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror("Error de Duplicado", f"Ya existe un concepto:\n\n  \"{concepto}\"\n\nen el grupo seleccionado.")
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
            
        # Cargar grupos
        grupos = self.cargar_grupos()
        if not grupos:
            messagebox.showwarning("Advertencia", "No hay grupos disponibles.")
            return
            
        valores = self.tree.item(selected[0])['values']
        conceptoid, concepto_actual, grupoid_fk_actual, grupo_nombre_actual = valores
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Concepto")
        dialog.geometry("500x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Concepto:").grid(row=0, column=0, sticky=tk.W, pady=5)
        concepto_var = tk.StringVar(value=concepto_actual)
        ttk.Entry(frame, textvariable=concepto_var, width=45).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(frame, text="Grupo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        grupo_fk_var = tk.StringVar()
        grupo_combo = ttk.Combobox(frame, textvariable=grupo_fk_var, width=43, state="readonly")
        grupo_dict = {f"{gid} - {nombre}": gid for gid, nombre in grupos}
        grupo_combo['values'] = list(grupo_dict.keys())
        # Preseleccionar el grupo actual si existe
        if grupoid_fk_actual:
            for key, val in grupo_dict.items():
                if val == grupoid_fk_actual:
                    grupo_combo.set(key)
                    break
        grupo_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def guardar():
            concepto = concepto_var.get().strip()
            grupo_fk_str = grupo_fk_var.get()
            
            if not concepto:
                messagebox.showwarning("Validación", "El nombre del concepto es obligatorio.")
                return
                
            grupoid_fk = grupo_dict.get(grupo_fk_str) if grupo_fk_str else None
            
            if not self.conectar():
                return
                
            try:
                self.cursor.execute(
                    "UPDATE conceptos SET concepto = %s, grupoid_fk = %s WHERE conceptoid = %s",
                    (concepto, grupoid_fk, conceptoid)
                )
                self.conn.commit()
                messagebox.showinfo("Éxito", "Concepto actualizado.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror("Error de Duplicado", f"Ya existe: \"{concepto}\" en el grupo seleccionado")
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
        conceptoid, concepto, grupoid_fk, grupo_nombre = valores
        
        count = self.validar_integridad(conceptoid)
        if count > 0:
            messagebox.showerror("⚠️ Registro en Uso",
                f"Este concepto está en {count} movimiento(s).\n\n  Concepto: \"{concepto}\"\n\n"
                "No se puede eliminar.")
            return
            
        if not messagebox.askyesno("Confirmar", f"¿Eliminar?\n\n  Concepto: \"{concepto}\""):
            return
            
        if not self.conectar():
            return
            
        try:
            self.cursor.execute("DELETE FROM conceptos WHERE conceptoid = %s", (conceptoid,))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Eliminado.")
            self.cargar_datos()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Error:\n{e}")
        finally:
            self.desconectar()
            
    def validar_integridad(self, conceptoid):
        if not self.conectar():
            return 0
        try:
            self.cursor.execute("SELECT COUNT(*) FROM movimientos WHERE ConceptoID = %s", (conceptoid,))
            return self.cursor.fetchone()[0]
        except:
            return 0
        finally:
            self.desconectar()


def main():
    root = tk.Tk()
    app = GestionarConceptosGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

