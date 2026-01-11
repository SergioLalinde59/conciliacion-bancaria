# AGREGAR AL FINAL DEL ARCHIVO asignar_clasificacion_movimiento_ui.py
# ANTES DE def main():

    def cargar_terceros_para_busqueda(self):
        """Carga la lista de terceros para el combobox de búsqueda."""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT terceroid, tercero
                FROM terceros
                WHERE activa = TRUE
                ORDER BY tercero
            """)
            
            terceros = cursor.fetchall()
            self.terceros_completos = terceros
            
            # Formato: "ID: Tercero"
            self.tercero_combo['values'] = [
                f"{tid}: {tercero}" 
                for tid, tercero in terceros
            ]
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.agregar_log(f"✗ Error al cargar terceros: {e}", 'error')
    
    def filtrar_terceros(self, event):
        """Filtra terceros mientras el usuario escribe."""
        texto_busqueda = self.tercero_combo.get().lower()
        
        if not hasattr(self, 'terceros_completos'):
            return
        
        if texto_busqueda:
            terceros_filtrados = [
                (tid, tercero) for tid, tercero in self.terceros_completos 
                if texto_busqueda in tercero.lower() or 
                   texto_busqueda in str(tid)
            ]
        else:
            terceros_filtrados = self.terceros_completos
        
        self.tercero_combo['values'] = [
            f"{tid}: {tercero}" 
            for tid, tercero in terceros_filtrados
        ]
    
    def on_tercero_seleccionado(self, event):
        """Maneja la selección de un tercero."""
        seleccion = self.tercero_combo.get()
        if seleccion and ':' in seleccion:
            # Extraer ID del formato "ID: Nombre"
            self.tercero_seleccionado_id = int(seleccion.split(':')[0])
            self.agregar_log(f"Tercero seleccionado: ID={self.tercero_seleccionado_id}", 'info')
            self.validar_actualizacion()
    
    def mostrar_busqueda_tercero(self):
        """Muestra el combo de búsqueda de tercero."""
        self.lbl_tercero_actual.grid_forget()
        self.btn_cambiar_tercero.grid_forget()
        self.tercero_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.btn_crear_tercero.grid(row=0, column=1, padx=2)
        self.cargar_terceros_para_busqueda()
    
    def crear_nuevo_tercero(self):
        """Abre diálogo para crear un nuevo tercero."""
        if not self.movimiento_actual:
            return
        
        mov_id, fecha, desc, ref, valor, tercero_id, grupo_id, concepto_id = self.movimiento_actual
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self.root)
        dialog.title("Crear Nuevo Tercero")
        dialog.geometry("500x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Campos - Solo nombre (después de 3NF, descripcion/referencia están en tercero_descripciones)
        ttk.Label(dialog, text="Tercero (requerido):", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        entry_tercero = ttk.Entry(dialog, width=40)
        entry_tercero.grid(row=0, column=1, padx=10, pady=10)
        
        # Mensaje de ayuda
        ttk.Label(dialog, text="El nombre del tercero debe ser único.", 
                 font=('Arial', 8, 'italic'), foreground='gray').grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        
        def guardar_tercero():
            tercero_nombre = entry_tercero.get().strip()
            
            if not tercero_nombre:
                messagebox.showerror("Error", "El campo 'Tercero' es requerido")
                return
            
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                
                # Insertar nuevo tercero (solo nombre)
                cursor.execute("""
                    INSERT INTO terceros (tercero)
                    VALUES (%s)
                    RETURNING terceroid
                """, (tercero_nombre,))
                
                nuevo_id = cursor.fetchone()[0]
                conn.commit()
                
                self.agregar_log(f"✓ Tercero creado: ID={nuevo_id}, {tercero_nombre}", 'success')
                
                cursor.close()
                conn.close()
                
                # Seleccionar el nuevo tercero
                self.tercero_seleccionado_id = nuevo_id
                self.tercero_combo.set(f"{nuevo_id}: {tercero_nombre}")
                
                # Recargar lista
                self.cargar_terceros_para_busqueda()
                
                # Validar actualización
                self.validar_actualizacion()
                
                dialog.destroy()
                messagebox.showinfo("Éxito", f"Tercero '{tercero_nombre}' creado correctamente")
                
            except psycopg2.IntegrityError as e:
                conn.rollback()
                self.agregar_log(f"✗ Error: Tercero duplicado - {e}", 'error')
                messagebox.showerror("Error", f"Ya existe un tercero con ese nombre:\n{e}")
            except Exception as e:
                conn.rollback()
                self.agregar_log(f"✗ Error al crear tercero: {e}", 'error')
                messagebox.showerror("Error", f"Error al crear tercero:\n{e}")
        
        # Botones
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Guardar", command=guardar_tercero, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy, width=15).grid(row=0, column=1, padx=5)
