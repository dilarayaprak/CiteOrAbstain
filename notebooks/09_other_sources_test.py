"""Test trafilatura on the other health sources (NHS, NIH NIAMS) + robots.txt check.

For each page:
  - does robots.txt allow us to fetch it?
  - does the site answer (status code)?
  - how much clean text does trafilatura extract, how does it start and end?
NHS splits topics into several sub-pages, so we also list the knee replacement
sub-pages found on the NHS hub page and test one of them.

Run from the project root (with venv active):
    python notebooks/09_other_sources_test.py
"""

import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
import trafilatura
from bs4 import BeautifulSoup

UA = "CiteOrAbstain student project (educational use)"
HEADERS = {"User-Agent": UA}

PAGES = {
    "NIH NIAMS - Joint Replacement Surgery": "https://www.niams.nih.gov/health-topics/joint-replacement-surgery",
    "NHS - Knee replacement (hub page)": "https://www.nhs.uk/conditions/knee-replacement/",
}


def robots_allowed(url):
    parts = urlparse(url)
    rp = RobotFileParser()
    rp.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        rp.read()
        return rp.can_fetch(UA, url)
    except Exception as e:
        return f"could not read robots.txt ({e})"


def test_page(name, url):
    print("=" * 78)
    print(f"{name}\n{url}")
    print(f"robots.txt allows: {robots_allowed(url)}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    print(f"status: {resp.status_code} | final URL: {resp.url}")
    if resp.status_code != 200:
        return resp
    text = trafilatura.extract(resp.content, url=resp.url, include_comments=False, include_tables=True) or ""
    print(f"clean text: {len(text):,} characters, {len(text.split()):,} words | bad chars ('â'): {text.count('â')}")
    print("--- FIRST 400 CHARACTERS ---")
    print(text[:400])
    print("--- LAST 250 CHARACTERS ---")
    print(text[-250:])
    print()
    return resp


responses = {}
for name, url in PAGES.items():
    responses[name] = test_page(name, url)
    time.sleep(2)  # polite pause between requests

# NHS: find knee replacement sub-pages on the hub page
hub = responses["NHS - Knee replacement (hub page)"]
if hub is not None and hub.status_code == 200:
    soup = BeautifulSoup(hub.content, "html.parser")
    hub_path = urlparse(hub.url).path.rstrip("/")
    subpages = []
    for a in soup.find_all("a", href=True):
        full = urljoin(hub.url, a["href"]).split("#")[0]
        path = urlparse(full).path.rstrip("/")
        if path.startswith(hub_path + "/") and full not in subpages:
            subpages.append(full)
    print("=" * 78)
    print(f"NHS knee replacement sub-pages found: {len(subpages)}")
    for s in subpages:
        print(f"  {s}")
    print()

    recovery = [s for s in subpages if "recovery" in s]
    if recovery:
        time.sleep(2)
        test_page("NHS - Knee replacement / Recovery (sub-page)", recovery[0])
