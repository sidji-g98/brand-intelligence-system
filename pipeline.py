import os, json, time
from dotenv import load_dotenv
from ddgs import DDGS
from google import genai

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    try:
        import streamlit as st
        API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
client = genai.Client(api_key=API_KEY)

def _generate(prompt, retries=3):
    for i in range(retries):
        try:
            return client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                time.sleep(60)
            else:
                raise
    raise RuntimeError("Rate-limited after retries - free quota likely used up for now.")

def _json(resp):
    return json.loads(resp.text.replace("```json", "").replace("```", "").strip())

def scout(brand, category, channel, competitors):
    queries = [
        f"best {category} brands {channel}",
        f"{brand} review",
        f"{brand} negative review complaint",
        f"{category} {channel} complaints not fresh",
    ] + [f"{c} review" for c in competitors]
    notes = []
    for q in queries:
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=6):
                notes.append(f"- {r['title']}: {r['body']}")
        time.sleep(1)
    prompt = f"""Market research for {brand} ({category} on {channel}).
From these notes, return ONLY JSON with keys: competitors, popular_products,
price_observations, common_praise, common_complaints, ad_headlines.
Notes:
{chr(10).join(notes)}"""
    return _json(_generate(prompt))

def analyse(brand, scout_data):
    prompt = f"""Senior analyst for {brand}. From this research JSON, return ONLY JSON with keys:
sentiment (object: positive, neutral, negative as ints summing to 100 - be REALISTIC, not over-positive),
praise_themes (list), complaint_themes (list),
competitor_positioning (list of objects with brand and positioning), key_insight (one sentence).
Research:
{json.dumps(scout_data, ensure_ascii=False)}"""
    return _json(_generate(prompt))

def strategise(brand, analyst_read, brand_voice):
    prompt = f"""Brand strategist for {brand}.
Brand voice/positioning (stay strictly on-brand):
{brand_voice}
Market read:
{json.dumps(analyst_read, ensure_ascii=False)}
Return ONLY JSON with keys: gap_analysis (list of objects with gap and why),
recommendations (exactly 3 objects with title, rationale, priority)."""
    return _json(_generate(prompt))

def write_content(brand, recommendations, brand_voice):
    prompt = f"""Copywriter for {brand}. Brand voice:
{brand_voice}
For each recommendation, draft on-brand content (never gym/hype).
Recommendations:
{json.dumps(recommendations, ensure_ascii=False)}
Return ONLY JSON: a list of objects with title, instagram_caption, amazon_headline, ad_hook."""
    return _json(_generate(prompt))

def run_pipeline(brand, category, channel, competitors, brand_voice, status=None):
    def say(m):
        if status: status(m)
    say("Scout: gathering live market data...")
    scout_data = scout(brand, category, channel, competitors)
    say("Analyst: reading the market...")
    read = analyse(brand, scout_data)
    say("Strategist: finding gaps and moves...")
    strategy = strategise(brand, read, brand_voice)
    say("Writer: drafting content...")
    content = write_content(brand, strategy["recommendations"], brand_voice)
    return {
        "scout": scout_data, "market_read": read,
        "gap_analysis": strategy["gap_analysis"],
        "recommendations": strategy["recommendations"],
        "draft_content": content,
    }