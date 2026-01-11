"""Script para agregar logging detallado a cargar_contexto_historico"""
import re

# Leer archivo
with open('asignar_clasificacion_movimiento_ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar y reemplazar la sección problemática
old_code = '''            self.contexto_historico = cursor.fetchall()
            
            # Limpiar TreeView de contexto
            for item in self.contexto_tree.get_children():
                self.contexto_tree.delete(item)
            
            # Poblar TreeView
            for ctx in self.contexto_historico:
                fecha, desc, ref, tercero, grupo, concepto, tid, gid, cid = ctx'''

new_code = '''            self.contexto_historico = cursor.fetchall()
            self.agregar_log(f"📊 DEBUG: Contexto={len(self.contexto_historico)} registros", 'info')
            
            # Limpiar TreeView de contexto
            for item in self.contexto_tree.get_children():
                self.contexto_tree.delete(item)
            
            # Poblar TreeView
            for idx, ctx in enumerate(self.contexto_historico):
                try:
                    self.agregar_log(f"📝 DEBUG: Procesando contexto[{idx}]...", 'info')
                    fecha, desc, ref, tercero, grupo, concepto, tid, gid, cid = ctx'''

if old_code in content:
    content = content.replace(old_code, new_code)
    
    # Agregar también logging después del unpacking
    old_insert = '''                self.contexto_tree.insert('', 'end', values=(
                    fecha.strftime('%Y-%m-%d'),'''
    
    new_insert = '''                    self.agregar_log(f"✓ Contexto[{idx}] OK", 'success')
                    self.contexto_tree.insert('', 'end', values=(
                        fecha.strftime('%Y-%m-%d'),'''
    
    content = content.replace(old_insert, new_insert)
    
    # Agregar catch de error
    old_log = '''            self.agregar_log(f"✓ Cargados {len(self.contexto_historico)} registros de contexto", 'success')'''
    new_log = '''                except Exception as ctx_err:
                    self.agregar_log(f"✗ ERROR ctx[{idx}]: {ctx_err}", 'error')
            
            self.agregar_log(f"✓ Cargados {len(self.contexto_historico)} registros de contexto", 'success')'''
    
    content = content.replace(old_log, new_log)
    
    # Guardar
    with open('asignar_clasificacion_movimiento_ui.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Logging agregado exitosamente")
else:
    print("✗ No se encontró el código a reemplazar")
