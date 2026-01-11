#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz de Gestión CRUD para Tabla Cuentas
Permite crear, leer, actualizar y eliminar registros de cuentas bancarias.

Autor: Antigravity
Fecha: 2025-12-29
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


class GestionarCuentasGUI:
    """Interfaz gráfica para gestionar cuentas bancarias."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Cuentas Bancarias")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.conn = None
        self.cursor = None
        self.registros = []
        self.registros_filtrados = []
        self.orden_ascendente = {}  # Para controlar orden de columnas
        
        self.setup_ui()
        self.cargar_datos()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Gestión de Cuentas Bancarias", 
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 15))
        
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
        
        # TreeView (DataGrid)
        columns = ("ID", "Cuenta")
        self.tree = ttk.Treeview(grid_frame, columns=columns, show="headings", height=15)
        
        # Configurar columnas
        self.tree.heading("ID", text="ID", command=lambda: self.ordenar_por_columna("ID"))
        self.tree.heading("Cuenta", text="Cuenta", command=lambda: self.ordenar_por_columna("Cuenta"))
        
        self.tree.column("ID", width=80, anchor=tk.CENTER)
        self.tree.column("Cuenta", width=400, anchor=tk.W)
        
        # Scrollbars
        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(grid_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Evento doble clic
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(button_frame, text="➕ Nueva Cuenta", 
                  command=self.nuevo_registro, width=20).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="✏️ Editar", 
                  command=self.editar_registro, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="🗑️ Eliminar", 
                  command=self.eliminar_registro, width=20).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="🔄 Actualizar", 
                  command=self.cargar_datos, width=20).grid(row=0, column=3, padx=5)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(status_frame, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.count_label = ttk.Label(status_frame, text="Total: 0", relief=tk.SUNKEN, anchor=tk.E)
        self.count_label.pack(side=tk.RIGHT)
        
    def conectar(self):
        """Conecta a la base de datos."""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos:\n{e}")
            return False
            
    def desconectar(self):
        """Cierra la conexión a la base de datos."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
    def cargar_datos(self):
        """Carga los registros desde la base de datos."""
        if not self.conectar():
            return
            
        try:
            self.cursor.execute("SELECT cuentaid, cuenta FROM cuentas ORDER BY cuentaid")
            self.registros = self.cursor.fetchall()
            self.registros_filtrados = self.registros.copy()
            self.actualizar_tree()
            self.status_label.config(text=f"✓ Datos cargados correctamente - {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos:\n{e}")
            self.status_label.config(text="✗ Error al cargar datos")
        finally:
            self.desconectar()
            
    def actualizar_tree(self):
        """Actualiza el TreeView con los datos filtrados."""
        # Limpiar TreeView
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Insertar registros filtrados
        for reg in self.registros_filtrados:
            self.tree.insert("", tk.END, values=reg)
            
        # Actualizar contador
        total = len(self.registros)
        mostrados = len(self.registros_filtrados)
        if total == mostrados:
            self.count_label.config(text=f"Total: {total}")
        else:
            self.count_label.config(text=f"Mostrando: {mostrados} de {total}")
            
    def filtrar_datos(self):
        """Filtra los registros según el texto de búsqueda."""
        termino = self.search_var.get().lower()
        
        if not termino:
            self.registros_filtrados = self.registros.copy()
        else:
            self.registros_filtrados = [
                reg for reg in self.registros
                if termino in str(reg[0]).lower() or termino in reg[1].lower()
            ]
            
        self.actualizar_tree()
        
    def ordenar_por_columna(self, columna):
        """Ordena los registros por la columna seleccionada."""
        col_index = {"ID": 0, "Cuenta": 1}[columna]
        
        # Alternar orden
        ascending = self.orden_ascendente.get(columna, True)
        self.orden_ascendente[columna] = not ascending
        
        # Ordenar
        self.registros_filtrados.sort(key=lambda x: x[col_index], reverse=not ascending)
        self.actualizar_tree()
        
    def on_double_click(self, event):
        """Maneja el doble clic en una fila."""
        self.editar_registro()
        
    def nuevo_registro(self):
        """Abre diálogo para crear un nuevo registro."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Nueva Cuenta")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Campo Cuenta
        ttk.Label(frame, text="Cuenta:").grid(row=0, column=0, sticky=tk.W, pady=5)
        cuenta_var = tk.StringVar()
        cuenta_entry = ttk.Entry(frame, textvariable=cuenta_var, width=40)
        cuenta_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        cuenta_entry.focus()
        
        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=20)
        
        def guardar():
            cuenta = cuenta_var.get().strip()
            
            if not cuenta:
                messagebox.showwarning("Validación", "El campo 'Cuenta' es obligatorio.")
                return
                
            if not self.conectar():
                return
                
            try:
                self.cursor.execute(
                    "INSERT INTO cuentas (cuenta) VALUES (%s)",
                    (cuenta,)
                )
                self.conn.commit()
                messagebox.showinfo("Éxito", "Cuenta creada exitosamente.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror(
                        "Error de Duplicado",
                        f"Ya existe una cuenta con el nombre:\n\n  \"{cuenta}\"\n\n"
                        "Por favor, ingrese un valor diferente."
                    )
                else:
                    messagebox.showerror("Error", f"Error de integridad:\n{e}")
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Error al crear registro:\n{e}")
            finally:
                self.desconectar()
                
        ttk.Button(button_frame, text="Guardar", command=guardar, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
    def editar_registro(self):
        """Abre diálogo para editar el registro seleccionado."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un registro para editar.")
            return
            
        # Obtener datos del registro seleccionado
        item = self.tree.item(selected[0])
        valores = item['values']
        cuentaid, cuenta_actual = valores[0], valores[1]
        
        # Diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Cuenta")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrar
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Frame
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Campo
        ttk.Label(frame, text="Cuenta:").grid(row=0, column=0, sticky=tk.W, pady=5)
        cuenta_var = tk.StringVar(value=cuenta_actual)
        cuenta_entry = ttk.Entry(frame, textvariable=cuenta_var, width=40)
        cuenta_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        cuenta_entry.select_range(0, tk.END)
        cuenta_entry.focus()
        
        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=20)
        
        def guardar():
            cuenta = cuenta_var.get().strip()
            
            if not cuenta:
                messagebox.showwarning("Validación", "El campo 'Cuenta' es obligatorio.")
                return
                
            if cuenta == cuenta_actual:
                dialog.destroy()
                return
                
            if not self.conectar():
                return
                
            try:
                self.cursor.execute(
                    "UPDATE cuentas SET cuenta = %s WHERE cuentaid = %s",
                    (cuenta, cuentaid)
                )
                self.conn.commit()
                messagebox.showinfo("Éxito", "Cuenta actualizada exitosamente.")
                dialog.destroy()
                self.cargar_datos()
            except IntegrityError as e:
                self.conn.rollback()
                if 'unique' in str(e).lower():
                    messagebox.showerror(
                        "Error de Duplicado",
                        f"Ya existe una cuenta con el nombre:\n\n  \"{cuenta}\"\n\n"
                        "Por favor, ingrese un valor diferente."
                    )
                else:
                    messagebox.showerror("Error", f"Error de integridad:\n{e}")
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Error al actualizar registro:\n{e}")
            finally:
                self.desconectar()
                
        ttk.Button(button_frame, text="Guardar", command=guardar, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
        
    def eliminar_registro(self):
        """Elimina el registro seleccionado después de validar integridad."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un registro para eliminar.")
            return
            
        # Obtener datos
        item = self.tree.item(selected[0])
        valores = item['values']
        cuentaid, cuenta = valores[0], valores[1]
        
        # Validar integridad
        count = self.validar_integridad(cuentaid)
        
        if count > 0:
            respuesta = messagebox.askyesno(
                "⚠️ Registro en Uso",
                f"⚠️ ADVERTENCIA: Este registro está siendo usado en {count} movimiento(s).\n\n"
                f"  Cuenta: \"{cuenta}\"\n\n"
                "No se puede eliminar un registro que está siendo referenciado.\n\n"
                "Para eliminarlo, primero debes eliminar o modificar los movimientos relacionados.",
                icon='warning'
            )
            return
            
        # Confirmar eliminación
        respuesta = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar este registro?\n\n"
            f"  Cuenta: \"{cuenta}\"\n\n"
            "Esta acción no se puede deshacer.",
            icon='question'
        )
        
        if not respuesta:
            return
            
        # Eliminar
        if not self.conectar():
            return
            
        try:
            self.cursor.execute("DELETE FROM cuentas WHERE cuentaid = %s", (cuentaid,))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Cuenta eliminada exitosamente.")
            self.cargar_datos()
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Error", f"Error al eliminar registro:\n{e}")
        finally:
            self.desconectar()
            
    def validar_integridad(self, cuentaid):
        """Verifica cuántos movimientos usan esta cuenta."""
        if not self.conectar():
            return 0
            
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM movimientos WHERE CuentaID = %s",
                (cuentaid,)
            )
            count = self.cursor.fetchone()[0]
            return count
        except Exception as e:
            print(f"Error al validar integridad: {e}")
            return 0
        finally:
            self.desconectar()


def main():
    """Función principal."""
    root = tk.Tk()
    app = GestionarCuentasGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
