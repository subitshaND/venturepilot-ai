import os, sys
sys.path.insert(0, r'D:\venturepilot-ai')
from prompts.startup_prompt import build_startup_prompt

sample = {
    "startup_name": "VenturePilot AI",
    "founder_name": "Subitsha N",
    "industry": "Technology",
    "startup_idea": "AI-powered startup blueprint generator using IBM Granite",
    "target_audience": "Students, entrepreneurs, and incubation centers",
    "business_stage": "Idea",
}
p = build_startup_prompt(sample)
print(f"Prompt chars : {len(p)}")
print(f"Approx tokens: {len(p) // 4}  (rough estimate at 4 chars/token)")
