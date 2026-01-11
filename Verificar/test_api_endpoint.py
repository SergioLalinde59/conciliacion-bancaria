
import requests

try:
    response = requests.get('http://localhost:8000/api/terceros/descripciones')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Items returned: {len(data)}")
        if len(data) > 0:
            print("First item:", data[0])
    else:
        print("Response:", response.text)
except Exception as e:
    print(f"Error connecting to API: {e}")
