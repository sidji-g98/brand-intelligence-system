import chromadb

# --- Your brand knowledge (edit or add to this anytime) ---
BRAND_DOCS = {
    "positioning": "Sweet Karam Coffee (SKC) is a Chennai-born direct-to-consumer brand reviving authentic South Indian snacks, traditional sweets, and signature filter coffee. Founded by Anand Bharadwaj and Nalini Parthiban, bootstrapped from Rs 2,000 to bring grandmother's recipes to modern homes. Core differentiator: clean-label purity with no palm oil, no preservatives, no maida, no artificial colours, no added white sugar. It sells nostalgia, authenticity and trust, not fitness or supplements.",
    "tone_of_voice": "Warm, nostalgic, homely, rooted in heritage and family, like a relative sharing a recipe. Leans into words like authentic, homemade, traditional, clean, fresh, nostalgia, grandmother's kitchen, festive, handcrafted. Avoids gym, macros, supplement, clinical, hype superlatives. Brand spirit: Experience South India, Let Good Make No Noise.",
    "product_claims": "Made without palm oil, preservatives, maida, artificial colours or flavours. Traditional recipes, fresh, homestyle. Snacks: murukku, ribbon pakoda, seedai, madras mixture, banana chips. Sweets: ghee mysore pak, athirasam, burfi, chikki. Signature in-house filter coffee (Arabica, Peaberry). Ready-to-eat meal mixes, pickles, papads, gift hampers. International shipping for the diaspora.",
    "target_audience": "Heritage seekers wanting authentic homestyle South Indian snacks online. Clean-label families avoiding palm oil and preservatives for kids and elders. NRIs and global Indians missing home flavours. Gifting buyers for festivals (Diwali, Pongal) and corporate hampers.",
    "past_campaigns": "Brand line Experience South India with hashtags ExperienceSouthIndia and LetGoodMakeNoise emphasising no palm oil and no preservatives. Founder story of bootstrapping from Rs 2,000 to a global brand reviving grandmother Janaki's recipes. Festival gifting pushes and colourful Chennai store launches.",
}

def chunk_text(text, size=500, overlap=100):
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks

def build_cabinet():
    client = chromadb.PersistentClient(path="chroma_db")
    try:
        client.delete_collection("brand_knowledge")  # rebuild fresh each run
    except Exception:
        pass
    collection = client.create_collection("brand_knowledge")

    docs, ids, metas = [], [], []
    for name, text in BRAND_DOCS.items():
        for i, chunk in enumerate(chunk_text(text)):
            docs.append(chunk)
            ids.append(f"{name}-{i}")
            metas.append({"source": name})

    collection.add(documents=docs, ids=ids, metadatas=metas)
    print(f"Loaded {len(docs)} chunks into the cabinet.")
    return collection

def ask_cabinet(collection, question, n=3):
    results = collection.query(query_texts=[question], n_results=n)
    snippets = results["documents"][0]
    sources = [m["source"] for m in results["metadatas"][0]]
    return list(zip(snippets, sources))

if __name__ == "__main__":
    cabinet = build_cabinet()
    questions = [
        "What is our tone of voice?",
        "What ingredients or benefits do we lead with?",
        "Who is our target customer?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        for snippet, source in ask_cabinet(cabinet, q):
            print(f"  [{source}] {snippet[:160].strip()}...")