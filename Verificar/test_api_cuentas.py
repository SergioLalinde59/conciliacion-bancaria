
import requests

try:
    response = requests.get('http://localhost:8000/api/cuentas')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
