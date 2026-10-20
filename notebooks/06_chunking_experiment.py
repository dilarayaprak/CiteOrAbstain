"""Experiment: splitting clean text into chunks (chunk size + overlap).

Steps:
  1) Download the MedlinePlus page and extract clean text with trafilatura
     (this time from raw bytes -> fixes the "Hereâs" encoding problem)
  2) Remove lines that are not useful for patients ("Updated by ...")
  3) Split the text into overlapping chunks with different settings
  4) Check how many tokens each chunk has vs. the embedding model's limit

Run from the project root (with venv active):
    python notebooks/06_chunking_experiment.py
"""

import requests
import trafilatura
from sentence_transformers import SentenceTransformer

URL = "https://medlineplus.gov/ency/article/002974.htm"

# ---------- 1) Download + extract (fixed encoding) ----------
headers = {"User-Agent": "CiteOrAbstain student project (educational use)"}
response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

text = trafilatura.extract(response.content, url=URL, include_comments=False, include_tables=True) or ""
print(f"Bad characters ('â') after fix: {text.count('â')}")

# ---------- 2) Remove non-patient lines ----------
lines = [ln for ln in text.splitlines() if ln.strip() and not ln.startswith("Updated by")]
clean_text = "\n".join(lines)
words = clean_text.split()
print(f"Clean text: {len(words):,} words\n")


# ---------- 3) Chunking function ----------
def chunk_words(words, size, overlap):
    """Split a list of words into chunks of `size` words.
    Each new chunk starts `size - overlap` words after the previous one,
    so neighbouring chunks share `overlap` words."""
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunk = words[start:start + size]
        chunks.append(" ".join(chunk))
        if start + size >= len(words):
            break
    return chunks


# ---------- 4) Token check with the embedding model ----------
model = SentenceTransformer("all-MiniLM-L6-v2")
limit = model.max_seq_length
print(f"Embedding model token limit (max_seq_length): {limit}\n")

print(f"{'size':>5} {'overlap':>8} {'chunks':>7} {'max tokens':>11} {'over limit':>11}")
print("-" * 46)
for size, overlap in [(100, 20), (150, 30), (200, 40), (400, 80)]:
    chunks = chunk_words(words, size, overlap)
    token_counts = [len(model.tokenizer(c)["input_ids"]) for c in chunks]
    over = sum(t > limit for t in token_counts)
    print(f"{size:>5} {overlap:>8} {len(chunks):>7} {max(token_counts):>11} {over:>11}")

# ---------- 5) Show what overlap looks like ----------
size, overlap = 150, 30
chunks = chunk_words(words, size, overlap)
print(f"\n=== Example with size={size}, overlap={overlap} ===")
print("\nEND OF CHUNK 1 (last 30 words):")
print(" ".join(chunks[0].split()[-overlap:]))
print("\nSTART OF CHUNK 2 (first 30 words):")
print(" ".join(chunks[1].split()[:overlap]))
