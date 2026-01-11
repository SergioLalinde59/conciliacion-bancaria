import traceback
import sys

try:
    exec(open('asignar_clasificacion_movimiento_ui.py', encoding='utf-8').read())
except Exception as e:
    print("=" * 80)
    print("ERROR CAPTURADO:")
    print("=" * 80)
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensaje: {e}")
    print("\nTraceback completo:")
    traceback.print_exc()
    print("=" * 80)
    sys.exit(1)
