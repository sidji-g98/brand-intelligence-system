import os, json
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from brand_cabinet import get_cabinet, ask_cabinet

load_dotenv()
BRAND = "Sweet Karam Coffee"

# Point CrewAI at Gemini (the gemini/ prefix tells it which provider)
llm = LLM(model="gemini/gemini-2.5-flash", api_key=os.environ["GEMINI_API_KEY"])

# --- Inputs: reuse what you already built ---
with open("scout_output.json", encoding="utf-8") as f:
    scout_data = json.load(f)

cabinet = get_cabinet()
ctx = []
for q in ["brand positioning and differentiation", "tone of voice", "target audience"]:
    for snippet, source in ask_cabinet(cabinet, q, n=2):
        ctx.append(f"[{source}] {snippet}")
brand_context = "\n".join(ctx)

# --- The agents (your AI team) ---
analyst = Agent(
    role="Market Analyst",
    goal=f"Turn raw market research on {BRAND} into a clear, realistic market read",
    backstory="A sharp FMCG analyst who finds the real signal in messy data.",
    llm=llm, verbose=True,
)
strategist = Agent(
    role="Brand Strategist",
    goal=f"Find positioning gaps and recommend 3 concrete moves for {BRAND}",
    backstory="A founder's-office strategist who turns insight into on-brand action.",
    llm=llm, verbose=True,
)
writer = Agent(
    role="Content Writer",
    goal=f"Draft ready-to-use, on-brand content for {BRAND}",
    backstory="A copywriter who nails the warm, heritage, clean-label voice.",
    llm=llm, verbose=True,
)

# --- The tasks (each feeds the next) ---
analyse_task = Task(
    description=f"Here is raw market research (JSON):\n{json.dumps(scout_data, ensure_ascii=False)}\n\n"
                "Produce a clear market read: a REALISTIC sentiment split, top praise themes, "
                "top complaint themes, and how the key competitors position themselves.",
    expected_output="A concise market read: sentiment, praise, complaints, competitor positioning.",
    agent=analyst,
)
strategise_task = Task(
    description=f"Using the market read AND this brand context (stay strictly on-brand):\n{brand_context}\n\n"
                "Identify 3 positioning gaps with evidence, and recommend exactly 3 concrete, prioritised moves.",
    expected_output="3 gaps (with evidence) and 3 prioritised recommendations (title + rationale).",
    agent=strategist, context=[analyse_task],
)
write_task = Task(
    description=f"For each of the 3 recommendations, draft on-brand content using this voice:\n{brand_context}\n\n"
                "Warm, heritage, clean-label - never gym/hype.",
    expected_output="For each recommendation: an Instagram caption, an Amazon headline, and an ad hook.",
    agent=writer, context=[strategise_task],
)

# --- Assemble and run the crew ---
crew = Crew(
    agents=[analyst, strategist, writer],
    tasks=[analyse_task, strategise_task, write_task],
    process=Process.sequential,
    verbose=True,
)

print(f"\nRunning the {BRAND} brand intelligence crew...\n")
result = crew.kickoff()

with open("brief.txt", "w", encoding="utf-8") as f:
    f.write(str(result))
print("\n=== FINAL BRIEF ===")
print(result)
print("\nSaved to brief.txt")