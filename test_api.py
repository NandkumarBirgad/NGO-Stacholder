import requests

response = requests.get('http://127.0.0.1:5000/api/projects')
print('Status Code:', response.status_code)
print('Response:', response.json())
