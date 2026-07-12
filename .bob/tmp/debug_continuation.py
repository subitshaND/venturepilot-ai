import sys
sys.path.insert(0, r'D:\venturepilot-ai')
from dotenv import load_dotenv
load_dotenv()
import os, requests

api_key = os.getenv('GRANITE_API_KEY', '')
api_url = os.getenv('GRANITE_API_URL', 'https://eu-de.ml.cloud.ibm.com').rstrip('/')
project_id = os.getenv('GRANITE_PROJECT_ID', '')

r = requests.post('https://iam.cloud.ibm.com/identity/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={'grant_type': 'urn:ibm:params:oauth:grant-type:apikey', 'apikey': api_key},
    timeout=30)
token = r.json()['access_token']

# Simulate what the loop does: call, get finish_reason, then Continue.
from prompts.startup_prompt import build_startup_prompt
prompt = build_startup_prompt({
    "startup_name": "VenturePilot AI", "founder_name": "Subitsha N",
    "industry": "Technology", "startup_idea": "AI-powered startup blueprint generator using IBM Granite",
    "target_audience": "Students, entrepreneurs, and incubation centers", "business_stage": "Idea",
})

messages = [{"role": "user", "content": prompt}]
parts = []

for i in range(1, 25):
    r2 = requests.post(f'{api_url}/ml/v1/text/chat?version=2024-05-31',
        headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'},
        json={
            "model_id": "ibm/granite-4-h-small",
            "project_id": project_id,
            "messages": messages,
            "parameters": {"max_new_tokens": 1024, "temperature": 0.5, "top_p": 0.95}
        },
        timeout=120)
    data = r2.json()
    choice = data['choices'][0]
    content = choice['message']['content']
    finish = choice.get('finish_reason')
    usage = data.get('usage', {})
    parts.append(content)
    print(f"Round {i}: finish={finish}  completion_tokens={usage.get('completion_tokens')}  chars={len(content)}")
    print(f"  Last 80: ...{content[-80:].strip()}")
    if finish != 'length':
        print(f"  -> Stopped naturally at round {i}")
        break
    messages.append({"role": "assistant", "content": content})
    messages.append({"role": "user", "content": "Continue."})

full = "".join(parts)
sections = [f"## {i}." for i in range(1, 11)]
missing = [s for s in sections if s not in full]
print(f"\nTotal chars: {len(full)}")
print(f"Missing sections: {missing if missing else 'None - all 10 present'}")
