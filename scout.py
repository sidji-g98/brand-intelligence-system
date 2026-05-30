import os, json, time
from dotenv import load_dotenv
from ddgs import DDGS
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

BRAND = "Sweet Karam Coffee"
CATEGORY = "traditional South Indian snacks"
CHANNEL = "Amazon India"
COMPETITORS = ["Haldiram's", "Grand Sweets and Snacks", "Beyond Snack", "Open Secret"]
ANGLE = "clean label no palm oil no preservatives no maida"

def web_search(query, max_results=8):
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))

def build_queries():
    q = [
        f"best {CATEGORY} brands {CHANNEL}",
        f"{BRAND} review",
        f"{BRAND} {CHANNEL} customer reviews",
        f"murukku mixture snacks {CHANNEL} reviews",
        f"{CATEGORY} {CHANNEL} complaints not fresh",
        f"{ANGLE} snacks India",
    ]
    for c in COMPETITORS:
        q.append(f"{c} snacks review")
    return q

def gather_raw_data():
    notes = []
    for query in build_queries():
        print("Searching:", query)
        for r in web_search(query):
            notes.append(f"- {r['title']}: {r['body']}")
        time.sleep(2)
    return "\n".join(notes)

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
    raise RuntimeError("Still rate-limited after retries - you've likely used today's free quota.")

def structure_findings(raw_text):
    prompt = f"""You are a market researcher studying {CATEGORY} on Amazon India.
Home brand: {BRAND}. Assess everyone against this lens: {ANGLE}.
From the raw search notes below, extract findings.
Return ONLY valid JSON (no commentary, no markdown) with these keys:
competitors, popular_products, price_observations,
common_praise, common_complaints, ad_headlines, clean_label_signals.
Each value should be a list of short strings.

Raw notes:
{raw_text}
"""
    resp = generate(prompt)
    clean = resp.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

print(f"\nScouting: {BRAND} - {CATEGORY} on {CHANNEL}\n")
raw = gather_raw_data()
data = structure_findings(raw)

print("\n--- FINDINGS ---")
print(json.dumps(data, indent=2, ensure_ascii=False))

with open("scout_output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("\nSaved scout_output.json")