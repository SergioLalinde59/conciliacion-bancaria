import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psycopg2
import sys
import os

sys.path.append(os.getcwd())

# Importar capas de Hexagonal
from src.infrastructure.database.postgres_movimiento_repository import PostgresMovimientoRepository
from src.infrastructure.extractors.bancolombia_adapter import BancolombiaAdapter
from src.application.services.cargar_movimientos_service import CargarMovimientosService

class CargarMovimientosHexagonalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cargar Movimientos (Versión Hexagonal)")
        self.root.geometry("600x400")
        
        self.archivo_path = tk.StringVar()
        
        # Conexión DB
        self.conn = psycopg2.connect(
            host='localhost', port='5433', database='Mvtos', user='postgres', password='SLB'
        )
        
        # Inicializar Componentes Hexagonales
        self.repo = PostgresMovimientoRepository(self.conn)
        self.service = CargarMovimientosService(self.repo)
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Sistema de Carga Hexagonal", font=("Arial", 16)).pack(pady=10)
        
        # Selección de archivo
        file_frame = ttk.LabelFrame(main_frame, text="Archivo PDF", padding="10")
        file_frame.pack(fill=tk.X, pady=10)
        
        ttk.Entry(file_frame, textvariable=self.archivo_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Buscar...", command=self.seleccionar_archivo).pack(side=tk.LEFT)
        
        # Botón de Carga
        self.btn_cargar = ttk.Button(main_frame, text="Procesar Archivo", command=self.procesar, state='disabled')
        self.btn_cargar.pack(pady=20)
        
        # Log
        self.log_lbl = ttk.Label(main_frame, text="Esperando archivo...", foreground="gray")
        self.log_lbl.pack()

    def seleccionar_archivo(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if filename:
            self.archivo_path.set(filename)
            self.btn_cargar.config(state='normal')

    def procesar(self):
        ruta = self.archivo_path.get()
        if not ruta: return
        
        self.log_lbl.config(text="Procesando...", foreground="blue")
        self.root.update_idletasks()
        
        try:
            # Seleccionar adaptador (en el futuro esto podría ser dinámico)
            adaptador = BancolombiaAdapter()
            
            # ID Cuenta 1 (Efectivo/Ahorros), ID Moneda 1 (Pesos) - Hardcoded por ahora para demo
            res = self.service.procesar_archivo(
                ruta_archivo=ruta, 
                lector=adaptador, 
                cuenta_id=1, 
                moneda_id=1
            )
            
            msg = f"Proceso Completado.\n\nTotal Leídos: {res['total_leidos']}\nNuevos: {res['nuevos']}\nDuplicados: {res['duplicados']}"
            if res['errores']:
                msg += f"\n\nErrores ({len(res['errores'])}): Ver consola."
                print(res['errores'])
            
            messagebox.showinfo("Resultado", msg)
            self.log_lbl.config(text="Carga Finalizada", foreground="green")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_lbl.config(text="Error en carga", foreground="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = CargarMovimientosHexagonalGUI(root)
    root.mainloop()
