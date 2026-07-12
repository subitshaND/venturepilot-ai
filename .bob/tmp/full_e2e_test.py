import sys, re
sys.path.insert(0, r'D:\venturepilot-ai')
from dotenv import load_dotenv
load_dotenv()

# ── 1. Test prompt building ───────────────────────────────────────────────────
from prompts.startup_prompt import build_startup_prompt
sample = {
    "startup_name":    "EduReach AI",
    "founder_name":    "Priya Sharma",
    "industry":        "EdTech",
    "startup_idea":    "AI-powered personalised learning platform for rural students with offline support",
    "target_audience": "Rural school students aged 10-18 and their teachers",
    "business_stage":  "Idea",
}
prompt = build_startup_prompt(sample)
assert "fenced code blocks" in prompt, "Prompt missing fence-block instruction"
assert "EduReach AI" in prompt
print(f"[PASS] Prompt built correctly ({len(prompt)} chars)")

# ── 2. Live API call ──────────────────────────────────────────────────────────
from services.granite_service import generate_startup_blueprint
print("\n[INFO] Calling IBM Granite (live)…")
ai_text = generate_startup_blueprint(sample)
print(f"[INFO] AI response received ({len(ai_text)} chars)")

# ── 3. Check no fenced tables slipped through ────────────────────────────────
fence_count = ai_text.count("```")
print(f"[INFO] Fenced-block markers (```) in response: {fence_count}")
if fence_count:
    print("[WARN] Model still used fenced blocks — fence-stripping in _parse_sections will handle it")
else:
    print("[PASS] No fenced code blocks in response")

# ── 4. Section parsing ────────────────────────────────────────────────────────
from app import _parse_sections
sections = _parse_sections(ai_text)
EXPECTED = [
    "business_summary", "business_model_canvas", "competitor_analysis",
    "swot_analysis", "estimated_budget", "funding_recommendations",
    "revenue_model", "gtm_strategy", "roadmap", "future_scope",
]
missing  = [k for k in EXPECTED if k not in sections or not sections[k]]
print(f"\n[INFO] Parsed sections: {list(sections.keys())}")
if missing:
    print(f"[FAIL] Missing/empty sections: {missing}")
else:
    print("[PASS] All 10 sections parsed")

# ── 5. HTML quality checks ────────────────────────────────────────────────────
failures = []
for key, html in sections.items():
    if "<pre>" in html and "<table>" not in html:
        failures.append(f"  {key}: rendered as <pre> (fenced block not stripped)")
    if not html.strip():
        failures.append(f"  {key}: empty HTML")

if failures:
    print("\n[FAIL] HTML quality issues:")
    for f in failures: print(f)
else:
    print("[PASS] No <pre> leakage — all content rendered as proper HTML")

# ── 6. Table check for sections that should have tables ──────────────────────
table_sections = ["business_model_canvas", "competitor_analysis", "estimated_budget", "roadmap"]
for k in table_sections:
    html = sections.get(k, "")
    if "<table>" in html:
        print(f"[PASS] {k}: contains <table>")
    else:
        print(f"[WARN] {k}: no <table> found (model may have used bullet points instead)")

# ── 7. Summary ────────────────────────────────────────────────────────────────
total_html = sum(len(v) for v in sections.values())
print(f"\n[SUMMARY]")
print(f"  Sections parsed  : {len(sections)}/10")
print(f"  Total HTML chars : {total_html}")
print(f"  Fenced blocks    : {fence_count}")
print(f"  Parse failures   : {len(failures)}")
if len(sections) == 10 and not failures:
    print("\n  ✓ App is working correctly end-to-end.")
else:
    print("\n  ✗ Issues detected — see above.")
