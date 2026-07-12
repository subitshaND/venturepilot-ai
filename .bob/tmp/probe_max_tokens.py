import requests, json, os, sys
sys.path.insert(0, r'D:\venturepilot-ai')
from dotenv import load_dotenv
from prompts.startup_prompt import build_startup_prompt
load_dotenv()

api_key = os.getenv('GRANITE_API_KEY', '')
api_url = os.getenv('GRANITE_API_URL', 'https://eu-de.ml.cloud.ibm.com').rstrip('/')
project_id = os.getenv('GRANITE_PROJECT_ID', '')

r = requests.post('https://iam.cloud.ibm.com/identity/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={'grant_type': 'urn:ibm:params:oauth:grant-type:apikey', 'apikey': api_key},
    timeout=30)
token = r.json()['access_token']

sample = {
    "startup_name": "VenturePilot AI",
    "founder_name": "Subitsha N",
    "industry": "Technology",
    "startup_idea": "AI-powered startup blueprint generator using IBM Granite",
    "target_audience": "Students, entrepreneurs, and incubation centers",
    "business_stage": "Idea",
}
prompt = build_startup_prompt(sample)

# Test incrementally: what is the max_new_tokens the API actually honours?
for tokens in [8000, 10000, 12000, 16000]:
    r2 = requests.post(f'{api_url}/ml/v1/text/chat?version=2024-05-31',
        headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'},
        json={
            "model_id": "ibm/granite-4-h-small",
            "project_id": project_id,
            "messages": [{"role": "user", "content": "Say hi."}],
            "parameters": {"max_new_tokens": tokens, "temperature": 0.1}
        },
        timeout=30)
    d = r2.json()
    status = r2.status_code
    if status == 200:
        print(f"max_new_tokens={tokens}: ACCEPTED  finish={d['choices'][0]['finish_reason']}  usage={d.get('usage')}")
    else:
        err = d.get('errors', d)
        print(f"max_new_tokens={tokens}: REJECTED  error={err}")
