import sys
sys.path.insert(0, r'D:\venturepilot-ai')
from services.granite_service import generate_startup_blueprint

result = generate_startup_blueprint({
    "startup_name": "VenturePilot AI",
    "founder_name": "Subitsha N",
    "industry": "Technology",
    "startup_idea": "AI-powered startup blueprint generator using IBM Granite",
    "target_audience": "Students, entrepreneurs, and incubation centers",
    "business_stage": "Idea",
})

# Check all 10 sections are present
sections = [f"## {i}." for i in range(1, 11)]
missing = [s for s in sections if s not in result]
print(f"\n--- VALIDATION ---")
print(f"Total chars : {len(result)}")
print(f"Missing sections: {missing if missing else 'None — all 10 present'}")
