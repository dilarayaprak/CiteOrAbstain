"""Compare three chunking methods by the RANK of the correct chunk.

The correct chunk for each question is defined objectively:
it is a chunk that CONTAINS a key sentence from the page.

Methods:
  A) plain word chunks over the whole page (week-2 Konu 3/4)
  B) section-aware chunks (Konu 5) - heading only in metadata
  C) section-aware chunks + "Title - Section:" header added to the text that is embedded

Run from the project root (with venv active):
    python notebooks/08b_chunking_methods_compare.py
"""

import requests
import trafilatura
from sentence_transformers import SentenceTransformer

URL = "https://medlineplus.gov/ency/article/002974.htm"
TITLE = "Knee joint replacement"
SIZE, OVERLAP = 120, 25
HEADINGS = {
    "Description", "Why the Procedure is Performed", "Risks", "Before the Procedure",
    "After the Procedure", "Outlook (Prognosis)", "Alternative Names", "References",
}
# question -> a key sentence that the correct chunk must contain
TESTS = {
    "Will I feel pain during the knee replacement surgery?": "You will not feel any pain during the surgery",
    "Why is knee replacement surgery done?": "The most common reason to have a knee joint replaced",
    "What should I do two weeks before surgery?": "During the 2 weeks before your surgery",
    "What is the artificial knee joint made of?": "Most artificial knees have both metal and plastic parts",
}

headers = {"User-Agent": "CiteOrAbstain student project (educational use)"}
html_bytes = requests.get(URL, headers=headers, timeout=30).content
text = trafilatura.extract(html_bytes, url=URL, include_comments=False, include_tables=True) or ""
lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("Updated by")]


def chunk_words(words, size, overlap):
    out = []
    for start in range(0, len(words), size - overlap):
        out.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return out


# A) whole page, headings stay inside the text
plain = chunk_words(" ".join(lines).split(), SIZE, OVERLAP)

# B) / C) section-aware
sections, current = [], ("Introduction", [])
for ln in lines:
    if ln in HEADINGS:
        if current[1]:
            sections.append(current)
        current = (ln, [])
    else:
        current[1].append(ln)
if current[1]:
    sections.append(current)
sections = [(n, b) for n, b in sections if n != "References"]

sec_chunks, sec_headers = [], []
for name, body in sections:
    for c in chunk_words(" ".join(body).split(), SIZE, OVERLAP):
        sec_chunks.append(c)
        sec_headers.append(f"{TITLE} - {name}: {c}")

METHODS = {
    "A) plain words": (plain, plain),
    "B) by section": (sec_chunks, sec_chunks),
    "C) section + header": (sec_chunks, sec_headers),   # (text to check, text to embed)
}

model = SentenceTransformer("all-MiniLM-L6-v2")
results = {}
for mname, (check_texts, embed_texts) in METHODS.items():
    vecs = model.encode(embed_texts)
    ranks = {}
    for q, key in TESTS.items():
        scores = model.similarity(model.encode(q), vecs)[0]
        order = scores.argsort(descending=True).tolist()
        correct = [i for i, t in enumerate(check_texts) if key in t]
        rank = min(order.index(i) for i in correct) + 1 if correct else None
        ranks[q] = (rank, float(scores[order[0]]))
    results[mname] = (len(check_texts), ranks)

print(f"Rank of the correct chunk (1 = best). Lower is better.\n")
print(f"{'question':<52} " + " ".join(f"{m:>20}" for m in METHODS))
for q in TESTS:
    row = []
    for m in METHODS:
        rank, _ = results[m][1][q]
        row.append(f"{('#' + str(rank)) if rank else 'not found':>20}")
    print(f"{q[:51]:<52} " + " ".join(row))

print()
for m, (n, ranks) in results.items():
    r = [rk for rk, _ in ranks.values() if rk]
    at1 = sum(1 for x in r if x == 1)
    at3 = sum(1 for x in r if x <= 3)
    print(f"{m:<22} chunks: {n:>3} | Recall@1: {at1}/{len(TESTS)} | Recall@3: {at3}/{len(TESTS)}")
