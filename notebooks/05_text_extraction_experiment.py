"""Experiment: extracting clean text from a real health web page.

Compares two methods on the same page:
  A) BeautifulSoup get_text()  -> takes ALL text on the page (menus, footer...)
  B) trafilatura.extract()     -> tries to keep only the main article content

Run from the project root (with venv active):
    python notebooks/05_text_extraction_experiment.py
"""

import requests
import trafilatura
from bs4 import BeautifulSoup

URL = "https://medlineplus.gov/ency/article/002974.htm"  # MedlinePlus: Knee joint replacement

# 1) Download the page (polite: one request, identify ourselves)
headers = {"User-Agent": "CiteOrAbstain student project (educational use)"}
response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()
html = response.text
print(f"Downloaded {len(html):,} characters of HTML from {URL}\n")

# 2) Method A: BeautifulSoup - all visible text
soup = BeautifulSoup(html, "html.parser")
text_a = soup.get_text(separator="\n", strip=True)

# 3) Method B: trafilatura - main content only
text_b = trafilatura.extract(html, url=URL, include_comments=False, include_tables=True) or ""

# 4) Compare
for name, text in [("A) BeautifulSoup", text_a), ("B) trafilatura", text_b)]:
    print("=" * 70)
    print(f"{name}: {len(text):,} characters, {len(text.split()):,} words")
    print("-" * 70)
    print("FIRST 500 CHARACTERS:")
    print(text[:500])
    print("...\nLAST 300 CHARACTERS:")
    print(text[-300:])
    print()
