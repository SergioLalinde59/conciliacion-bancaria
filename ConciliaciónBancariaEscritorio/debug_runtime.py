"""Debug runtime - simular selección de movimiento"""
import tkinter as tk
from tkinter import ttk
import asignar_clasificacion_movimiento_ui as ui_module

print("Creating GUI...")
root = tk.Tk()
root.withdraw()

app = ui_module.AsignarClasificacionGUI(root)

print(f"\nVerificando widgets después de init:")
print(f"  tercero_combo: {app.tercero_combo}")
print(f"  btn_crear_tercero: {app.btn_crear_tercero}")
print(f"  btn_cambiar_tercero: {app.btn_cambiar_tercero}")

# Simular selección de movimiento ID 1656
print("\n" + "=" * 80)
print("Simulando carga de movimiento ID=1656...")
print("=" * 80)

try:
    app.cargar_movimiento_completo(1656)
    print("\n✓ Movimiento cargado sin errores")
except Exception as e:
    print(f"\n✗ ERROR al cargar movimiento:")
    print(f"  Tipo: {type(e).__name__}")
    print(f"  Mensaje: {e}")
    import traceback
    traceback.print_exc()

root.destroy()
