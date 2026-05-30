import os, json, time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

BRAND = "Sweet Karam Coffee"
CATEGORY = "traditional South Indian snacks"

# Load the Scout's findings
with open("scout_output.json", encoding="utf-8") as f:
    scout = json.load(f)

def generate(prompt, retries=3):
    for i in range(retries):
        try:
            return client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print(f"Hit Google's rate limit, waiting 60s... (try {i+1}/{retries})")
                time.sleep(60)
            else:
                raise
    raise RuntimeError("Still rate-limited after retries.")

def analyse(scout_data):
    prompt = f"""You are a senior brand analyst studying {CATEGORY}.
Home brand: {BRAND}.
Below is structured market research collected by a research agent (as JSON).
Interpret it and produce a clear market read.

Return ONLY valid JSON (no commentary, no markdown) with these keys:
- sentiment: an object with positive, neutral, negative as integer percentages adding up to 100 (estimate from the praise/complaint balance and any ratings)
- praise_themes: 4-6 consolidated themes customers love (short phrases)
- complaint_themes: 3-5 consolidated complaint themes (short phrases; infer likely ones if the data is thin)
- competitor_positioning: a list of objects, each with "brand" and "positioning" (one line each) for the 5-6 most relevant competitors
- clean_label_landscape: 2-3 sentences on who owns clean-label messaging and where the open gap is for {BRAND}
- key_insight: one punchy sentence - the single most important strategic takeaway

Research data:
{json.dumps(scout_data, ensure_ascii=False)}
"""
    resp = generate(prompt)
    clean = resp.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

print(f"\nAnalysing market read for {BRAND}...\n")
read = analyse(scout)

print(json.dumps(read, indent=2, ensure_ascii=False))

with open("analyst_output.json", "w", encoding="utf-8") as f:
    json.dump(read, f, indent=2, ensure_ascii=False)
print("\nSaved analyst_output.json")