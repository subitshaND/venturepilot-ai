import requests, json, os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('GRANITE_API_KEY', '')
api_url = os.getenv('GRANITE_API_URL', 'https://eu-de.ml.cloud.ibm.com').rstrip('/')
project_id = os.getenv('GRANITE_PROJECT_ID', '')

r = requests.post('https://iam.cloud.ibm.com/identity/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={'grant_type': 'urn:ibm:params:oauth:grant-type:apikey', 'apikey': api_key},
    timeout=30)
token = r.json()['access_token']

# Send a minimal test chat to inspect stop_reason and usage
r2 = requests.post(f'{api_url}/ml/v1/text/chat?version=2024-05-31',
    headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'},
    json={
        "model_id": "ibm/granite-4-h-small",
        "project_id": project_id,
        "messages": [{"role": "user", "content": "Say hello in exactly 5 words."}],
        "parameters": {"max_new_tokens": 20, "temperature": 0.1}
    },
    timeout=30)
data = r2.json()
print("status:", r2.status_code)
print("stop_reason:", data.get('choices', [{}])[0].get('finish_reason'))
print("usage:", data.get('usage'))
print("full response keys:", list(data.keys()))

# Now test with max_new_tokens = 8000
r3 = requests.post(f'{api_url}/ml/v1/text/chat?version=2024-05-31',
    headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'},
    json={
        "model_id": "ibm/granite-4-h-small",
        "project_id": project_id,
        "messages": [{"role": "user", "content": "Say hello in exactly 5 words."}],
        "parameters": {"max_new_tokens": 8000, "temperature": 0.1}
    },
    timeout=30)
data3 = r3.json()
print("\nWith max_new_tokens=8000 - status:", r3.status_code)
if r3.status_code != 200:
    print("error:", data3)
else:
    print("ok - stop_reason:", data3.get('choices', [{}])[0].get('finish_reason'))
