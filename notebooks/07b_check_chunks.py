"""Quick check: print the FULL top-3 chunks for two questions, for two models.
Goal: see whether the best-scoring chunk really answers the question.

Run from the project root (with venv active):
    python notebooks/07b_check_chunks.py
"""

import requests
import trafilatura
from sentence_transformers import SentenceTransformer

URL = "https://medlineplus.gov/ency/article/002974.htm"
QUESTIONS = [
    "Will I feel pain during the knee replacement surgery?",
    "Why is knee replacement surgery done?",
]
MODELS = ["all-MiniLM-L6-v2", "all-mpnet-base-v2"]

headers = {"User-Agent": "CiteOrAbstain student project (educational use)"}
html_bytes = requests.get(URL, headers=headers, timeout=30).content
text = trafilatura.extract(html_bytes, url=URL, include_comments=False, include_tables=True) or ""
lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("Updated by")]
words = "\n".join(lines).split()

SIZE, OVERLAP = 120, 25
chunks = []
for start in range(0, len(words), SIZE - OVERLAP):
    chunks.append(" ".join(words[start:start + SIZE]))
    if start + SIZE >= len(words):
        break

for name in MODELS:
    model = SentenceTransformer(name)
    chunk_vecs = model.encode(chunks)
    for q in QUESTIONS:
        scores = model.similarity(model.encode(q), chunk_vecs)[0]
        top = scores.argsort(descending=True)[:3]
        print("=" * 78)
        print(f"MODEL: {name}\nQUESTION: {q}")
        for rank, i in enumerate(top, start=1):
            print(f"\n  #{rank}  chunk {int(i)}  score {float(scores[i]):.2f}")
            print(f"  {chunks[int(i)]}")
        print()
