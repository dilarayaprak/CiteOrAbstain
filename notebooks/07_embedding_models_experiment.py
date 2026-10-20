"""Experiment: comparing embedding models on real chunks.

Same MedlinePlus page, chunked with the recommended setting (120 words, 25 overlap).
For each model we check:
  - basic facts: vector size, token limit, speed
  - for each question: best matching chunk and its similarity score
  - the GAP between answerable and unanswerable questions
    (bigger gap = easier to choose an abstain threshold)

Run from the project root (with venv active):
    python notebooks/07_embedding_models_experiment.py
Note: the first run downloads the two new models (~90 MB and ~420 MB).
"""

import time

import requests
import trafilatura
from sentence_transformers import SentenceTransformer

URL = "https://medlineplus.gov/ency/article/002974.htm"

MODELS = [
    "all-MiniLM-L6-v2",           # what we use now (general purpose, small)
    "multi-qa-MiniLM-L6-cos-v1",  # same size, trained on question -> answer pairs
    "all-mpnet-base-v2",          # bigger general purpose model
]

ANSWERABLE = [
    "What is the artificial knee joint made of?",
    "Will I feel pain during the knee replacement surgery?",
    "Why is knee replacement surgery done?",
]
UNANSWERABLE = [
    "What is the capital of France?",
    "How much does knee replacement cost in Turkey?",
]

# ---------- Text + chunks ----------
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
print(f"{len(chunks)} chunks of ~{SIZE} words (overlap {OVERLAP})\n")

# ---------- Compare models ----------
summary = []
for name in MODELS:
    t0 = time.time()
    model = SentenceTransformer(name)
    load_s = time.time() - t0

    t0 = time.time()
    chunk_vecs = model.encode(chunks)
    encode_s = time.time() - t0

    print("=" * 78)
    print(f"MODEL: {name}")
    print(f"vector size: {model.get_sentence_embedding_dimension()} | token limit: {model.max_seq_length} "
          f"| load: {load_s:.1f}s | encode {len(chunks)} chunks: {encode_s:.2f}s")
    print("-" * 78)

    best = {}
    for q in ANSWERABLE + UNANSWERABLE:
        scores = model.similarity(model.encode(q), chunk_vecs)[0]
        i = int(scores.argmax())
        best[q] = float(scores[i])
        tag = "ANS" if q in ANSWERABLE else "NO "
        print(f"[{tag}] {best[q]:.2f}  {q}")
        print(f"        -> {chunks[i][:90]}...")

    lowest_ans = min(best[q] for q in ANSWERABLE)
    highest_no = max(best[q] for q in UNANSWERABLE)
    gap = lowest_ans - highest_no
    summary.append((name, lowest_ans, highest_no, gap))
    print(f"\nlowest answerable: {lowest_ans:.2f} | highest unanswerable: {highest_no:.2f} | GAP: {gap:.2f}\n")

print("=" * 78)
print("SUMMARY (bigger GAP = easier to set an abstain threshold)")
print(f"{'model':<28} {'lowest ANS':>11} {'highest NO':>11} {'GAP':>7}")
for name, la, hn, gap in summary:
    print(f"{name:<28} {la:>11.2f} {hn:>11.2f} {gap:>7.2f}")
