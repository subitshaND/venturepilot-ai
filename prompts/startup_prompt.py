"""
startup_prompt.py
Prompt templates for VenturePilot AI startup analysis.
"""


def build_startup_prompt(startup_data: dict) -> str:
    """
    Construct the prompt to be sent to IBM Granite for startup analysis.

    Args:
        startup_data (dict): Fields collected from the startup form.
            Expected keys:
                - startup_name (str)
                - founder_name (str)
                - industry (str)
                - startup_idea (str)
                - target_audience (str)
                - business_stage (str)

    Returns:
        str: Fully formatted prompt string.
    """
    startup_name = startup_data.get("startup_name", "N/A")
    founder_name = startup_data.get("founder_name", "N/A")
    industry = startup_data.get("industry", "N/A")
    startup_idea = startup_data.get("startup_idea", "N/A")
    target_audience = startup_data.get("target_audience", "N/A")
    business_stage = startup_data.get("business_stage", "N/A")

    prompt = f"""You are an experienced Startup Consultant and Business Strategist. Generate a complete, investor-ready startup analysis report using the details below. Be concise but thorough. Use bullet points and plain markdown tables where appropriate. Do not invent facts. Do NOT wrap any content in fenced code blocks (no ```markdown, no ```). All tables must be written as plain markdown tables directly in the text.

Startup Name: {startup_name}
Founder: {founder_name}
Industry: {industry}
Idea: {startup_idea}
Target Audience: {target_audience}
Stage: {business_stage}

Generate all 10 sections below. Each section must be complete before moving to the next.

## 1. Executive Summary
Write 4-5 sentences covering the problem, solution, target market, stage, and why this venture is worth pursuing.

## 2. Business Model Canvas
Fill a markdown table with all 9 blocks: Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, Cost Structure.

## 3. Competitor Analysis
Create a table with columns: Competitor Type | Strengths | Weaknesses | Differentiation Opportunity for {startup_name}. Cover both direct and indirect competitors in the {industry} space.

## 4. SWOT Analysis
Create a 2x2 table: Strengths, Weaknesses, Opportunities, Threats. List 3 bullet points per quadrant.

## 5. Estimated Budget
Create a table with columns: Category | Estimated Cost (USD) | Notes. Cover: Product/Tech Development, Marketing, Operations, Team/Salaries, Legal, Contingency, Total. Base on a {business_stage}-stage {industry} startup. State assumptions.

## 6. Funding and Investor Recommendations
- Suitable funding sources for this stage
- Types of investors likely interested
- A 3-sentence pitch narrative for {founder_name}
- 3-5 key metrics investors look for

## 7. Revenue Model
- Primary and secondary revenue streams
- Pricing strategy
- Year 1 / Year 2 / Year 3 revenue projections with assumptions

## 8. Go-To-Market Strategy
- Beachhead segment within {target_audience}
- Top 3-5 acquisition channels
- Pre-launch, launch, post-launch phases
- Key partnerships
- 3 KPIs for the first 90 days

## 9. Six-Month Roadmap
Create a table: Month | Milestone | Key Activities | Success Metric. Cover months 1-6 for a {business_stage}-stage startup.

## 10. Future Scope
- 2-3 product/service expansions
- Adjacent markets for Years 2-3
- Emerging {industry} trends {startup_name} can leverage
- Long-term vision (2-3 sentences)
"""

    return prompt
