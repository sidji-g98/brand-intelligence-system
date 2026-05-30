import streamlit as st
import plotly.graph_objects as go
from pipeline import run_pipeline

st.set_page_config(page_title="Brand Intelligence System", layout="wide")
st.title("Brand Intelligence System")
st.caption("Autonomous category teardown, powered by AI agents")

with st.sidebar:
    st.header("Inputs")
    brand = st.text_input("Brand", "Sweet Karam Coffee")
    category = st.text_input("Category", "traditional South Indian snacks")
    channel = st.text_input("Channel", "Amazon India")
    competitors_raw = st.text_input("Competitors (comma-separated)",
        "Haldiram's, Grand Sweets and Snacks, Beyond Snack, Open Secret")
    brand_voice = st.text_area("Brand positioning & voice",
        "Sweet Karam Coffee revives authentic South Indian snacks with no palm oil, "
        "no preservatives, no maida. Warm, heritage, clean-label tone - never gym/hype.",
        height=160)
    run = st.button("Run analysis", type="primary")

if run:
    competitors = [c.strip() for c in competitors_raw.split(",") if c.strip()]
    box = st.status("Starting the agents...", expanded=True)
    try:
        result = run_pipeline(brand, category, channel, competitors, brand_voice,
                              status=lambda m: box.update(label=m))
        box.update(label="Done", state="complete")
    except Exception as e:
        box.update(label="Error", state="error")
        st.error(str(e)); st.stop()

    read = result["market_read"]
    s = read.get("sentiment", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Competitors found", len(result["scout"].get("competitors", [])))
    c2.metric("Positive sentiment", f"{s.get('positive','?')}%")
    c3.metric("Recommendations", len(result["recommendations"]))

    t1, t2, t3 = st.tabs(["Market Read", "Strategy", "Draft Content"])
    with t1:
        if s:
            fig = go.Figure(data=[go.Pie(labels=["Positive", "Neutral", "Negative"],
                values=[s.get("positive",0), s.get("neutral",0), s.get("negative",0)], hole=.5)])
            fig.update_layout(height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        st.subheader("What customers love")
        for x in read.get("praise_themes", []): st.write("•", x)
        st.subheader("Common complaints")
        for x in read.get("complaint_themes", []): st.write("•", x)
        if read.get("key_insight"): st.info(read["key_insight"])
    with t2:
        st.subheader("Positioning gaps")
        for g in result["gap_analysis"]:
            st.markdown(f"**{g.get('gap','')}** — {g.get('why','')}")
        st.subheader("Recommendations")
        for r in result["recommendations"]:
            st.markdown(f"**Priority {r.get('priority','')}: {r.get('title','')}** — {r.get('rationale','')}")
    with t3:
        for c in result["draft_content"]:
            st.markdown(f"### {c.get('title','')}")
            st.write("**Instagram:**", c.get("instagram_caption",""))
            st.write("**Amazon headline:**", c.get("amazon_headline",""))
            st.write("**Ad hook:**", c.get("ad_hook",""))