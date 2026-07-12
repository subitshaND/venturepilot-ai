import requests, json, os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('GRANITE_API_KEY', '')
api_url = os.getenv('GRANITE_API_URL', 'https://eu-de.ml.cloud.ibm.com').rstrip('/')

r = requests.post('https://iam.cloud.ibm.com/identity/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={'grant_type': 'urn:ibm:params:oauth:grant-type:apikey', 'apikey': api_key},
    timeout=30)
token = r.json()['access_token']

r2 = requests.get(f'{api_url}/ml/v1/foundation_model_specs?version=2024-05-31&limit=200',
    headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'},
    timeout=30)

for m in r2.json().get('resources', []):
    if m['model_id'] == 'ibm/granite-4-h-small':
        print(json.dumps(m, indent=2))
