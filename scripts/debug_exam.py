import requests
import json

url = 'http://localhost:8000/v1/exam/generate'
headers = {'X-Internal-Key': 'dev_secret_key_12345', 'Content-Type': 'application/json'}
data = {
    'board': 'CBSE',
    'class': 10,
    'subject': 'Physics',
    'chapters': ['Light', 'Electricity'],
    'totalQuestions': 3,
    'bloomsDistribution': {'Understand': 100},
    'difficulty': 'Medium'
}

print('Testing Understand level only...')
try:
    response = requests.post(url, headers=headers, json=data, timeout=60)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print(f'Generated: {result["totalQuestions"]} questions')
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")