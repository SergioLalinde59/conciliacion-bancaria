"""Script de debug para encontrar el error de tercero_combo"""
import sys
import traceback

# Agregar logging detallado
import tkinter as tk
from tkinter import ttk

print("=" * 80)
print("INICIANDO DEBUG")
print("=" * 80)

try:
    # Importar y ejecutar
    import asignar_clasificacion_movimiento_ui as ui_module
    
    print("Módulo importado correctamente")
    print(f"Clases en módulo: {[x for x in dir(ui_module) if not x.startswith('_')]}")
    
    # Intentar crear la GUI
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana
    
    print("\nCreando instancia de AsignarClasificacionGUI...")
    app = ui_module.AsignarClasificacionGUI(root)
    
    print("\n✓ Instancia creada exitosamente")
    print(f"✓ app.tercero_combo existe: {hasattr(app, 'tercero_combo')}")
    print(f"✓ app.tercero_combo es None: {app.tercero_combo is None if hasattr(app, 'tercero_combo') else 'NO EXISTE'}")
    
    if hasattr(app, 'tercero_combo') and app.tercero_combo:
        print(f"✓ tercero_combo widget: {app.tercero_combo}")
    
    root.destroy()
    print("\n✓ DEBUG COMPLETO - NO HAY ERRORES EN INICIALIZACIÓN")
    
except Exception as e:
    print("\n" + "=" * 80)
    print("✗ ERROR ENCONTRADO:")
    print("=" * 80)
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensaje: {e}")
    print("\nTraceback completo:")
    print("=" * 80)
    traceback.print_exc()
    print("=" * 80)
    sys.exit(1)
