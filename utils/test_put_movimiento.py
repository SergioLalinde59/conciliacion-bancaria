import json

# Payload de prueba para actualizar movimiento
payload = {
    "fecha": "2025-12-31",
    "descripcion": "Prueba Hexagonal",
    "referencia": "REF-TEST-HEX-001",
    "valor": 0.0,
    "usd": None,
    "trm": None,
    "moneda_id": 1,
    "cuenta_id": 1,
    "tercero_id": None,
    "grupo_id": 1,
    "concepto_id": 1
}

print("Payload a enviar:")
print(json.dumps(payload, indent=2))

# Simular la llamada
import urllib.request
import urllib.error

url = "http://localhost:8000/api/movimientos/1947"
data = json.dumps(payload).encode('utf-8')

req = urllib.request.Request(url, data=data, headers={
    'Content-Type': 'application/json'
}, method='PUT')

try:
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        print("\n✅ Respuesta exitosa:")
        print(result)
except urllib.error.HTTPError as e:
    print(f"\n❌ Error HTTP {e.code}:")
    print(e.read().decode('utf-8'))
except urllib.error.URLError as e:
    print(f"\n❌ Error de conexión:")
    print(e.reason)
except Exception as e:
    print(f"\n❌ Error inesperado:")
    print(f"{type(e).__name__}: {e}")
