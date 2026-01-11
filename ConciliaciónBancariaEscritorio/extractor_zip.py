#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extractor de Archivos ZIP
Extrae todos los archivos de múltiples ZIPs a un directorio de destino.
Con renombrado automático de archivos PDF y XLS.
"""

import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
from datetime import datetime
import threading
import re


class ZipExtractorGUI:
    # Mapeo de meses en español a números
    MONTHS_ES = {
        'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04',
        'MAY': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
        'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor de Archivos ZIP")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        
        # Variables
        self.source_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.custom_name = tk.StringVar()
        self.is_processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="Extractor de Archivos ZIP", 
                                font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # Carpeta de origen (ZIPs)
        ttk.Label(main_frame, text="Carpeta con archivos ZIP:").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.source_folder, width=50).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Buscar...", command=self.select_source_folder).grid(
            row=1, column=2, padx=5)
        
        # Carpeta de destino
        ttk.Label(main_frame, text="Carpeta de destino:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.dest_folder, width=50).grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Buscar...", command=self.select_dest_folder).grid(
            row=2, column=2, padx=5)
        
        # Nombre personalizado (opcional)
        ttk.Label(main_frame, text="Nombre personalizado (opcional):").grid(
            row=3, column=0, sticky=tk.W, pady=5)
        custom_entry = ttk.Entry(main_frame, textvariable=self.custom_name, width=50)
        custom_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Label(main_frame, text="📝", font=("Arial", 10)).grid(
            row=3, column=2, padx=5)
        
        # Ayuda para nombre personalizado
        help_label = ttk.Label(main_frame, 
                               text="Ej: '2025-01 7796' (sin extensión, se agregará automáticamente)",
                               font=("Arial", 8), foreground="gray")
        help_label.grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5)
        
        # Botón de extracción
        self.extract_button = ttk.Button(main_frame, text="Extraer y Renombrar Archivos", 
                                         command=self.start_extraction)
        self.extract_button.grid(row=5, column=0, columnspan=3, pady=15)
        
        # Área de log
        log_frame = ttk.LabelFrame(main_frame, text="Registro de Actividad", padding="5")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70, 
                                                   wrap=tk.WORD, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Texto de estado
        self.status_label = ttk.Label(main_frame, text="Listo para comenzar", 
                                      foreground="green")
        self.status_label.grid(row=8, column=0, columnspan=3, pady=5)
        
    def select_source_folder(self):
        """Selecciona la carpeta donde están los archivos ZIP"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta con archivos ZIP")
        if folder:
            self.source_folder.set(folder)
            self.log(f"Carpeta de origen seleccionada: {folder}")
            
    def select_dest_folder(self):
        """Selecciona la carpeta de destino"""
        folder = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if folder:
            self.dest_folder.set(folder)
            self.log(f"Carpeta de destino seleccionada: {folder}")
            
    def log(self, message):
        """Agrega un mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
        
    def update_status(self, message, color="black"):
        """Actualiza el texto de estado"""
        self.status_label.config(text=message, foreground=color)
        self.root.update_idletasks()
    
    def rename_file(self, original_name):
        """Renombra archivo según patrón NUMERO_MESAÑO.ext -> YYYY-MM NNNN.ext
        
        Args:
            original_name: Nombre original del archivo
            
        Returns:
            Nombre renombrado o nombre original si no coincide con el patrón
        """
        # Si hay un nombre personalizado definido, usarlo
        if self.custom_name.get().strip():
            custom = self.custom_name.get().strip()
            ext = Path(original_name).suffix
            # Si el custom ya tiene extensión, usarlo tal cual
            if '.' in custom:
                return custom
            # Si no, agregar la extensión del archivo original
            return f"{custom}{ext}"
        
        # Solo procesar PDF y XLS/XLSX
        ext = Path(original_name).suffix.lower()
        if ext not in ['.pdf', '.xls', '.xlsx']:
            return original_name
        
        # Patrón: NUMERO_MESAÑO.ext
        # Ejemplos: 7796_ENE2025.pdf, 10270076377_ENE2025.pdf, 437000004144_FEB2025.xls
        pattern = r'^(\d+)_([A-Z]{3})(\d{4})\.(pdf|xls|xlsx)$'
        match = re.match(pattern, original_name, re.IGNORECASE)
        
        if not match:
            self.log(f"  ⚠️ No coincide con patrón de renombrado: {original_name}")
            return original_name
        
        numero, mes_abr, año, extension = match.groups()
        
        # Extraer últimos 4 dígitos del número
        numero_corto = numero[-4:]
        
        # Convertir mes abreviado a número
        mes_abr_upper = mes_abr.upper()
        if mes_abr_upper not in self.MONTHS_ES:
            self.log(f"  ⚠️ Mes no reconocido: {mes_abr}")
            return original_name
        
        mes_num = self.MONTHS_ES[mes_abr_upper]
        
        # Generar nuevo nombre: YYYY-MM NNNN.ext
        new_name = f"{año}-{mes_num} {numero_corto}.{extension}"
        
        self.log(f"  🔄 Renombrado: {original_name} → {new_name}")
        
        return new_name
        
    def start_extraction(self):
        """Inicia el proceso de extracción en un hilo separado"""
        if self.is_processing:
            messagebox.showwarning("Advertencia", "Ya hay una extracción en proceso.")
            return
            
        # Validar carpetas
        if not self.source_folder.get():
            messagebox.showerror("Error", "Por favor selecciona la carpeta con archivos ZIP.")
            return
        if not self.dest_folder.get():
            messagebox.showerror("Error", "Por favor selecciona la carpeta de destino.")
            return
            
        if not os.path.exists(self.source_folder.get()):
            messagebox.showerror("Error", "La carpeta de origen no existe.")
            return
            
        # Crear carpeta de destino si no existe
        os.makedirs(self.dest_folder.get(), exist_ok=True)
        
        # Ejecutar en hilo separado para no bloquear la UI
        self.is_processing = True
        self.extract_button.config(state='disabled')
        thread = threading.Thread(target=self.extract_files, daemon=True)
        thread.start()
        
    def extract_files(self):
        """Extrae todos los archivos de los ZIPs encontrados"""
        try:
            source_path = Path(self.source_folder.get())
            dest_path = Path(self.dest_folder.get())
            
            # Buscar todos los archivos ZIP
            zip_files = list(source_path.glob("*.zip")) + list(source_path.glob("*.ZIP"))
            
            if not zip_files:
                self.log("⚠️ No se encontraron archivos ZIP en la carpeta seleccionada.")
                messagebox.showwarning("Advertencia", 
                                       "No se encontraron archivos ZIP en la carpeta seleccionada.")
                return
            
            self.log(f"📦 Se encontraron {len(zip_files)} archivo(s) ZIP")
            self.log("-" * 60)
            
            # Configurar barra de progreso
            self.progress_bar['maximum'] = len(zip_files)
            self.progress_bar['value'] = 0
            
            total_extracted = 0
            errors = []
            
            # Procesar cada archivo ZIP
            for idx, zip_file in enumerate(zip_files, 1):
                try:
                    self.update_status(f"Procesando {idx}/{len(zip_files)}: {zip_file.name}", 
                                       "blue")
                    self.log(f"\n📁 Procesando: {zip_file.name}")
                    
                    # Verificar que es un ZIP válido
                    if not zipfile.is_zipfile(zip_file):
                        self.log(f"  ⚠️ El archivo no es un ZIP válido, se omite.")
                        errors.append(f"{zip_file.name}: No es un ZIP válido")
                        continue
                    
                    # Extraer archivos
                    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                        file_list = zip_ref.namelist()
                        self.log(f"  📄 Contiene {len(file_list)} archivo(s)")
                        
                        for file_name in file_list:
                            # Extraer solo el nombre del archivo (sin rutas internas)
                            base_name = os.path.basename(file_name)
                            
                            # Saltar directorios
                            if not base_name or file_name.endswith('/'):
                                continue
                            
                            # Renombrar archivo si es PDF o XLS
                            renamed_file = self.rename_file(base_name)
                            
                            # Leer el contenido del archivo
                            file_content = zip_ref.read(file_name)
                            
                            # Escribir en el destino con el nuevo nombre (sobrescribe si existe)
                            dest_file = dest_path / renamed_file
                            with open(dest_file, 'wb') as f:
                                f.write(file_content)
                            
                            total_extracted += 1
                        
                        self.log(f"  ✅ Extraído correctamente")
                    
                except Exception as e:
                    error_msg = f"{zip_file.name}: {str(e)}"
                    self.log(f"  ❌ Error: {str(e)}")
                    errors.append(error_msg)
                
                # Actualizar barra de progreso
                self.progress_bar['value'] = idx
                
            # Resumen final
            self.log("-" * 60)
            self.log(f"\n🎉 Proceso completado!")
            self.log(f"   Total de archivos extraídos: {total_extracted}")
            self.log(f"   Carpeta de destino: {dest_path}")
            
            if errors:
                self.log(f"\n⚠️ Se encontraron {len(errors)} error(es):")
                for error in errors:
                    self.log(f"   - {error}")
            
            # Mostrar mensaje final
            if errors:
                self.update_status("Completado con errores", "orange")
                messagebox.showwarning("Completado con errores", 
                                       f"Se extrajeron {total_extracted} archivos.\n"
                                       f"Se encontraron {len(errors)} error(es).\n"
                                       f"Revisa el registro para más detalles.")
            else:
                self.update_status("Completado exitosamente", "green")
                messagebox.showinfo("Éxito", 
                                    f"¡Proceso completado!\n\n"
                                    f"Total de archivos extraídos: {total_extracted}\n"
                                    f"Carpeta de destino: {dest_path}")
            
        except Exception as e:
            self.log(f"\n❌ Error crítico: {str(e)}")
            self.update_status("Error crítico", "red")
            messagebox.showerror("Error", f"Error crítico durante la extracción:\n{str(e)}")
            
        finally:
            self.is_processing = False
            self.extract_button.config(state='normal')
            self.progress_bar['value'] = 0


def main():
    """Función principal"""
    root = tk.Tk()
    app = ZipExtractorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
