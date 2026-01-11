import re

file_path = 'asignar_clasificacion_movimiento_ui.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new method content
new_method = """    def cargar_contexto_historico(self, fecha_mov, referencia_mov, patron, tercero_id, grupo_id, concepto_id):
        \"\"\"Carga los 5 registros anteriores completos.\"\"\"
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Obtener descripción del movimiento actual para búsqueda por similitud
            desc_mov = \"\"
            if self.movimiento_actual:
                desc_mov = self.movimiento_actual[2]
            
            # Estrategia de búsqueda de contexto:
            # 1. Si hay referencia -> Buscar por referencia
            # 2. Si NO hay referencia -> Buscar por similitud en descripción (ej. \"Traslado A Fondo\")
            
            if referencia_mov:
                cursor.execute(\"\"\"
                    SELECT m.Fecha, m.Descripcion, m.Referencia, 
                           t.tercero, g.grupo, c.concepto,
                           m.TerceroID, m.GrupoID, m.ConceptoID
                    FROM movimientos m
                    LEFT JOIN terceros t ON m.TerceroID = t.terceroid
                    LEFT JOIN grupos g ON m.GrupoID = g.grupoid
                    LEFT JOIN conceptos c ON m.ConceptoID = c.conceptoid
                    WHERE m.Referencia = %s
                      AND m.Fecha < %s
                      AND m.TerceroID IS NOT NULL
                    ORDER BY m.Fecha DESC
                    LIMIT 5
                \"\"\", (referencia_mov, fecha_mov))
                self.agregar_log(f\"🔍 Buscando contexto con referencia: {referencia_mov}\", 'info')
            else:
                palabras = desc_mov.split()
                prefijo = \" \".join(palabras[:2]) if len(palabras) >= 2 else (palabras[0] if palabras else \"\")
                
                cursor.execute(\"\"\"
                    SELECT m.Fecha, m.Descripcion, m.Referencia, 
                           t.tercero, g.grupo, c.concepto,
                           m.TerceroID, m.GrupoID, m.ConceptoID
                    FROM movimientos m
                    LEFT JOIN terceros t ON m.TerceroID = t.terceroid
                    LEFT JOIN grupos g ON m.GrupoID = g.grupoid
                    LEFT JOIN conceptos c ON m.ConceptoID = c.conceptoid
                    WHERE m.Descripcion LIKE %s
                      AND m.Fecha < %s
                      AND m.TerceroID IS NOT NULL
                    ORDER BY m.Fecha DESC
                    LIMIT 5
                \"\"\", (f\"%{prefijo}%\", fecha_mov))
                self.agregar_log(f\"🔍 Buscando contexto por descripción similar: {prefijo}...\", 'info')
            
            self.contexto_historico = cursor.fetchall()
            
            # Limpiar TreeView de contexto
            for item in self.contexto_tree.get_children():
                self.contexto_tree.delete(item)
            
            # Poblar TreeView
            for idx, ctx in enumerate(self.contexto_historico):
                try:
                    c_fecha, c_desc, c_ref, c_tercero, c_grupo, c_concepto, c_tid, c_gid, c_cid = ctx
                    self.contexto_tree.insert('', 'end', values=(
                        c_fecha.strftime('%Y-%m-%d'),
                        c_desc[:40],
                        c_ref if c_ref else '',
                        c_tercero if c_tercero else '',
                        c_grupo if c_grupo else '',
                        c_concepto if c_concepto else ''
                    ))
                except Exception as ctx_err:
                    self.agregar_log(f\"✗ ERROR procesando fila de contexto: {ctx_err}\", 'error')
            
            self.agregar_log(f\"✓ Cargados {len(self.contexto_historico)} registros de contexto relevante\", 'success')
            
            # --- MANEJO DE TERCERO ---
            if tercero_id:
                cursor.execute(\"SELECT tercero FROM terceros WHERE terceroid = %s\", (tercero_id,))
                res = cursor.fetchone()
                tercero_nombre = res[0] if res else \"Desconocido\"
                
                self.lbl_tercero_actual.config(text=f\"{tercero_id}: {tercero_nombre}\", foreground='black')
                self.lbl_tercero_actual.grid(row=0, column=0, sticky=tk.W)
                self.btn_cambiar_tercero.grid(row=0, column=1, padx=2)
                self.tercero_combo.grid_forget()
                self.btn_crear_tercero.grid_forget()
                self.tercero_seleccionado_id = tercero_id
            else:
                self.lbl_tercero_actual.config(text=\"(Sin asignar)\", foreground='red')
                self.lbl_tercero_actual.grid_forget()
                
                if self.tercero_combo:
                    self.tercero_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
                    self.btn_crear_tercero.grid(row=0, column=1, padx=2)
                    self.btn_cambiar_tercero.grid_forget()
                    
                    self.agregar_log(f\"🔍 Buscando terceros similares para: '{desc_mov}'\", 'info')
                    self.cargar_terceros_para_busqueda(desc_mov)
                
                self.tercero_seleccionado_id = None
            
            # Cargar y analizar grupos y conceptos
            self.cargar_grupos_conceptos(grupo_id, concepto_id)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.agregar_log(f\"✗ Error al cargar contexto: {e}\", 'error')
"""

# Regexp to find the method and replace it
# It looks for def cargar_contexto_historico and goes until the next def or end of class
pattern = r'    def cargar_contexto_historico\(self, fecha_mov, referencia_mov, patron, tercero_id, grupo_id, concepto_id\):(.*?)(?=\n    def|\nclass|\Z)'
modified_content = re.sub(pattern, new_method, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(modified_content)

print("Method cargar_contexto_historico updated successfully")
