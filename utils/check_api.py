import requests

# Verificar estructura de cada endpoint
endpoints = {
    'cuentas': 'http://localhost:8000/api/cuentas',
    'monedas': 'http://localhost:8000/api/monedas',
    'terceros': 'http://localhost:8000/api/terceros',
    'grupos': 'http://localhost:8000/api/grupos',
}

for name, url in endpoints.items():
    print(f"\n{'='*50}")
    print(f"Endpoint: {name}")
    print('='*50)
    try:
        res = requests.get(url)
        data = res.json()
        if data:
            print(f"Total items: {len(data)}")
            print(f"Primer elemento:")
            print(f"  Campos: {list(data[0].keys())}")
            print(f"  Valores: {data[0]}")
    except Exception as e:
        print(f"Error: {e}")
