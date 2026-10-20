"""Experiment: storing REAL chunks in ChromaDB with rich source metadata.

New compared to week 1:
  - real text (MedlinePlus) instead of hand-written sentences
  - section-aware chunking: split by section headings first, then by size
  - metadata per chunk: url, title, source, section, chunk index
  - cosine distance set explicitly when the collection is created
  - separate collection ("medlineplus_test") so the week-1 demo is untouched

Run from the project root (with venv active):
    python notebooks/08_chromadb_real_chunks.py
"""

import chromadb
import requests
import trafilatura
from sentence_transformers import SentenceTransformer

URL = "https://medlineplus.gov/ency/article/002974.htm"
SOURCE = "MedlinePlus"
TITLE = "Knee joint replacement"
SIZE, OVERLAP = 120, 25

# Section headings on this MedlinePlus page (kept by trafilatura as separate lines)
HEADINGS = {
    "Description", "Why the Procedure is Performed", "Risks", "Before the Procedure",
    "After the Procedure", "Outlook (Prognosis)", "Alternative Names", "References",
}

# ---------- 1) Extract clean text ----------
headers = {"User-Agent": "CiteOrAbstain student project (educational use)"}
html_bytes = requests.get(URL, headers=headers, timeout=30).content
text = trafilatura.extract(html_bytes, url=URL, include_comments=False, include_tables=True) or ""
lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("Updated by")]

# ---------- 2) Group lines into sections ----------
sections = []          # list of (section_name, [lines])
current = ("Introduction", [])
for ln in lines:
    if ln in HEADINGS:
        if current[1]:
            sections.append(current)
        current = (ln, [])
    else:
        current[1].append(ln)
if current[1]:
    sections.append(current)

# The reference list is not patient information -> skip it
sections = [(name, body) for name, body in sections if name != "References"]


# ---------- 3) Chunk each section separately ----------
def chunk_words(words, size, overlap):
    chunks = []
    for start in range(0, len(words), size - overlap):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return chunks


ids, documents, metadatas = [], [], []
for name, body in sections:
    for j, chunk in enumerate(chunk_words(" ".join(body).split(), SIZE, OVERLAP)):
        ids.append(f"medlineplus-002974-{len(ids):03d}")
        documents.append(chunk)
        metadatas.append({"url": URL, "title": TITLE, "source": SOURCE,
                          "section": name, "chunk_in_section": j})

print(f"{len(sections)} sections -> {len(documents)} chunks")
for name, body in sections:
    n = sum(1 for m in metadatas if m["section"] == name)
    print(f"  {name:<32} {len(' '.join(body).split()):>4} words -> {n} chunk(s)")

# ---------- 4) Store in ChromaDB (cosine) ----------
model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="chroma_db")
try:
    client.delete_collection("medlineplus_test")   # start fresh on every run
except Exception:
    pass
collection = client.create_collection(name="medlineplus_test", metadata={"hnsw:space": "cosine"})
collection.add(ids=ids, documents=documents, metadatas=metadatas,
               embeddings=model.encode(documents).tolist())
print(f"\nStored {collection.count()} chunks in collection 'medlineplus_test'\n")

# ---------- 5) Search ----------
QUESTIONS = [
    "Will I feel pain during the knee replacement surgery?",
    "Why is knee replacement surgery done?",
    "What should I do two weeks before surgery?",
    "How much does knee replacement cost in Turkey?",
]
for q in QUESTIONS:
    res = collection.query(query_embeddings=[model.encode(q).tolist()], n_results=3)
    print("=" * 78)
    print(f"QUESTION: {q}")
    for rank, (doc, meta, dist) in enumerate(zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), 1):
        print(f"  #{rank}  similarity {1 - dist:.2f} | {meta['source']} > {meta['section']} (part {meta['chunk_in_section']})")
        print(f"       {doc[:110]}...")
    top = res["metadatas"][0][0]
    print(f"  CITATION: {top['source']}, \"{top['title']}\", section \"{top['section']}\" - {top['url']}")
