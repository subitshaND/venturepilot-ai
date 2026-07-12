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
    "startup_name": "VenturePilot AI", "founder_name": "Subitsha N",
    "industry": "Technology", "startup_idea": "AI-powered startup blueprint generator using IBM Granite",
    "target_audience": "Students, entrepreneurs, and incubation centers", "business_stage": "Idea",
}
from prompts.startup_prompt import build_startup_prompt
prompt = build_startup_prompt(sample)

r2 = requests.post(f'{api_url}/ml/v1/text/chat?version=2024-05-31',
    headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'},
    json={
        "model_id": "ibm/granite-4-h-small",
        "project_id": project_id,
        "messages": [{"role": "user", "content": prompt}],
        "parameters": {"max_new_tokens": 16000, "temperature": 0.5, "top_p": 0.95}
    },
    timeout=120)
data = r2.json()
choice = data['choices'][0]
usage = data.get('usage', {})
print(f"finish_reason : {choice['finish_reason']}")
print(f"prompt_tokens : {usage.get('prompt_tokens')}")
print(f"completion_tokens: {usage.get('completion_tokens')}")
print(f"total_tokens  : {usage.get('total_tokens')}")
content = choice['message']['content']
print(f"output chars  : {len(content)}")
print(f"last 200 chars: ...{content[-200:]}")
