import re

with open('asignar_clasificacion_movimiento_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Corregir el bucle de contexto para no sobrescribir 'desc'
# Buscamos la sección de poblar TreeView que tiene el error de lógica
old_context_loop = r'for idx, ctx in enumerate\(self\.contexto_historico\):\s+try:\s+self\.agregar_log\(f"📝 DEBUG: Procesando contexto\[\{idx\}\]\.\.\.", \'info\'\)\s+fecha, desc, ref, tercero, grupo, concepto, tid, gid, cid = ctx'
new_context_loop = 'for idx, ctx in enumerate(self.contexto_historico):\n                try:\n                    c_fecha, c_desc, c_ref, c_tercero, c_grupo, c_concepto, c_tid, c_gid, c_cid = ctx'

content = re.sub(old_context_loop, new_context_loop, content)

# 2. Corregir las referencias a las variables dentro del insert del TreeView
content = content.replace("fecha.strftime('%Y-%m-%d'),", "c_fecha.strftime('%Y-%m-%d'),")
content = content.replace("desc[:40],", "c_desc[:40],")
content = content.replace("ref if ref else '',", "c_ref if c_ref else '',")
content = content.replace("tercero if tercero else '',", "c_tercero if c_tercero else '',")
content = content.replace("grupo if grupo else '',", "c_grupo if c_grupo else '',")
content = content.replace("concepto if concepto else ''", "c_concepto if c_concepto else ''")

# 3. Corregir la búsqueda de contexto para cuando NO hay referencia
old_context_query = r'else:\s+# Sin filtro específico\s+cursor\.execute\("""\s+SELECT m\.Fecha, m\.Descripcion, m\.Referencia, \s+t\.tercero, g\.grupo, c\.concepto,\s+m\.TerceroID, m\.GrupoID, m\.ConceptoID\s+FROM movimientos m\s+LEFT JOIN terceros t ON m\.TerceroID = t\.terceroid\s+LEFT JOIN grupos g ON m\.GrupoID = g\.grupoid\s+LEFT JOIN conceptos c ON m\.ConceptoID = c\.conceptoid\s+WHERE m\.Fecha < %s\s+AND m\.TerceroID IS NOT NULL\s+AND m\.GrupoID IS NOT NULL\s+AND m\.ConceptoID IS NOT NULL\s+ORDER BY m\.Fecha DESC\s+LIMIT 5\s+""", \(fecha_mov,\)\)'
new_context_query = '''            else:
                # Sin referencia: Buscar movimientos con descripción similar (ej. "Traslado A Fondo")
                palabra_clave = desc_mov.split()[0] if desc_mov else ""
                cursor.execute("""
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
                """, (f"{palabra_clave}%", fecha_mov))'''

content = re.sub(old_context_query, new_context_query, content)

# 4. Asegurar que se usa desc_mov para la carga de terceros
content = re.sub(r'self\.cargar_terceros_para_busqueda\(desc\)', r'self.cargar_terceros_para_busqueda(desc_mov)', content)
content = re.sub(r"description: '\{desc\[:50\]\}\.\.\.'", r"description: '{desc_mov[:50]}...'", content)

with open('asignar_clasificacion_movimiento_ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Correcciones de contexto y variables aplicadas")
