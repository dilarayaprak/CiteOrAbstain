# Technology Decisions

This document records the technologies chosen for CiteOrAbstain, the decisions made and the reasons behind them. Decisions are based on research and small experiments carried out in weeks 1 and 2. All experiment code is in `notebooks/`.

A Turkish version of this document is available: [technology_decisions_TR.md](technology_decisions_TR.md)

Author: Dilara Yaprak — Last updated: October 2026 (week 2)

## Decision Summary

| Area | Choice | Status |
|---|---|---|
| Programming language | Python 3.12 | Final |
| Dependency management | `requirements.txt` (pinned direct dependencies) + lock file | Final (lock file proposed) |
| Version control | GitHub, branch + Pull Request workflow | Final (team rules proposed) |
| Text extraction | `requests` (raw bytes) + `trafilatura` | Provisional (tested on 3 sources) |
| Chunking | Section-aware, ~120 words, 25-word overlap, ≤ 256 tokens | Provisional (to be validated on the question set) |
| Embedding | sentence-transformers, `all-MiniLM-L6-v2` (candidate: `all-mpnet-base-v2`) | Provisional |
| Vector database | ChromaDB, cosine similarity | Provisional (team approval pending) |
| Retrieval | Top-K = 5 | Provisional |
| LLM (local) | Ollama + `llama3.2` (3B) | Provisional |
| LLM (hosted) | Not chosen yet | Open |
| Web UI | Streamlit | Final |
| Containerization | Docker Compose | Final (written at the end of the project) |
| Question language | English | Provisional (advisor confirmation pending) |

**Status meaning:** *Final* = not expected to change. *Provisional* = we proceed with it but it may change. *Open* = not decided yet.

---

## 1. Programming Language and Environment

**Choice:** Python 3.12, one virtual environment (`venv`) per computer.

- The project brief recommends Python; every component (embedding, vector database, LLM client, Streamlit) has a Python library.
- **Why 3.12?** Newer versions (3.13, 3.14) carry compatibility risks with heavy libraries such as PyTorch and onnxruntime. 3.12 works with all of them. The final Docker image will use the same version.
- **Virtual environment (venv):** Each computer has its own isolated environment. It is never pushed to GitHub (`.gitignore`); everyone recreates it from `requirements.txt`.
- **Always use `python -m pip`** instead of `pip`. Some antivirus programs block the `pip.exe` file inside the venv.

### Dependency management

- `requirements.txt` pins only the libraries we use directly (e.g. `chromadb==1.5.9`, `sentence-transformers==6.1.0`).
- **Problem observed:** Indirect dependencies are not pinned and can change between installations. On the old computer `transformers 5.18.0` was installed, on the new computer `transformers 5.20.1`. It caused no problem this time, but this is a typical cause of "it works on my computer but not on yours".
- **Proposal:** Keep an additional lock file with the exact versions of everything in a working environment:
  `python -m pip freeze > requirements-lock.txt`
  `requirements.txt` stays the short, human-readable list; Docker and the jury setup can use the lock file. The lock file may contain Windows-only packages, so it must be tested in Docker (Linux).
- **To be added this week:** `requests`, `trafilatura==2.3.1`. (`beautifulsoup4` is not needed by the final pipeline.)

### Known environment issue: Windows 11 Smart App Control

- On a new Windows 11 computer, Smart App Control switched from *evaluation* to *on* automatically and blocked an unsigned DLL inside numpy:
  `ImportError: DLL load failed while importing _pcg64: Uygulama Denetimi ilkesi bu dosyayı engelledi.`
  The same libraries had worked the day before.
- **Fix:** Windows Security → App & browser control → Smart App Control → *Off*. Windows Defender antivirus keeps running.
- **Trade-off:** Once turned off, it cannot be turned back on without reinstalling Windows. Team members with Windows 11 may face the same issue.

## 2. Version Control and Team Workflow

**Choice:** GitHub repository `dilarayaprak/CiteOrAbstain` (private), with a branch + Pull Request workflow.

- **Branch:** A separate line of work that does not touch `main` until it is reviewed.
- **Pull Request (PR):** A request to merge a branch into `main`. Teammates review it, comment, and approve.
- **Why:** `main` always contains working code; every change is reviewed by at least one other person; the review history is visible on GitHub (code quality is 35% of the grade).

```text
main ──●──────────────●──────  (stable code everyone uses)
        \            /
         ●──●──●───●          (working branch)
                   ↑
             Pull Request
```

**Proposed team rules:**
1. No direct pushes to `main`; all work happens on a branch named `name/topic` (e.g. `dilara/week2-research`).
2. Every PR is merged only after **at least one teammate approves** it.
3. On joint coding days, the team works on one shared branch (e.g. `feature/retrieval-v0`) and opens a PR at the end of the day.
4. Two people do not edit the same file independently at the same time.
5. Everyone runs `git pull` before starting work.

Setup steps for teammates are in [kurulum_rehberi.md](kurulum_rehberi.md).

## 3. Text Extraction from Web Pages

**Problem:** A downloaded web page is HTML, not plain text. Besides the article it contains menus, site banners and footers. If this "noise" is not removed, it becomes chunks in the database and can be returned as search results.

**Choice:** Download with `requests`, extract the main content with `trafilatura`, passing the **raw bytes** (`response.content`).

### Experiment 1: BeautifulSoup vs trafilatura (`05_text_extraction_experiment.py`)

Page: MedlinePlus — Knee joint replacement (https://medlineplus.gov/ency/article/002974.htm)

| | A) BeautifulSoup `get_text()` | B) trafilatura `extract()` |
|---|---|---|
| Length | 11,736 characters (1,911 words) | 7,342 characters (1,282 words) |
| Starts with | "Skip navigation", "An official website of the United States government", lock icon text | The article itself: "Knee joint replacement is a surgery to replace a knee joint..." |
| Ends with | Footer: "NLM Web Policies", "Copyright", postal address | "Updated by: ... 07/01/2025" |

- About one third of the BeautifulSoup text (~4,400 characters, ~37%) was noise.
- trafilatura removed it automatically and kept section headings ("Description") and bullet points.

**Encoding problem:** BeautifulSoup output showed "Hereâs how you know" instead of "Here's how you know". The site does not declare its character encoding, so `requests` guessed wrong and broke UTF-8 characters. Broken words ("don't", "patient's") reduce embedding and search quality.
**Fix:** Pass raw bytes (`response.content`) to trafilatura; it detects the encoding itself. After the fix, the number of broken characters was **0** (`06_chunking_experiment.py`).

### Experiment 2: Other sources (`09_other_sources_test.py`)

| Source | Result |
|---|---|
| **NHS** hub page (`/conditions/knee-replacement/`) | Redirected to `/tests-and-treatments/knee-replacement/`. Only 24 words: it is a table of contents. Content is on **7 sub-pages**: what-is-a-knee-replacement, why-its-done, alternatives, preparation, how-its-done, recovery, complications. |
| **NHS** Recovery sub-page | Very clean: 563 words, starts with the heading, no broken characters. Ends with noise lines: "Video: ...", "In this video, ...", "Media review due: 22 May 2029". |
| **NIH NIAMS** `/health-topics/joint-replacement-surgery` | **Silently redirected** to the general topics list (`/health-topics`). Extracted 160 words of site banner and general text, not knee replacement content. Status code was still 200. |

### Findings and rules for the pipeline

1. **trafilatura works well** on MedlinePlus and NHS content pages.
2. **Check the final URL and the text length,** not only the status code. A redirect or a very short text (e.g. < 200 words) must produce a warning.
3. **Each NHS sub-page is a separate source.** NHS alone provides 7 sources. Use the current `/tests-and-treatments/...` addresses.
4. **Remove site-specific noise lines:** "Updated by ..." (MedlinePlus), "Video: ...", "In this video, ...", "Media review due: ..." (NHS). Keep the update date in the source registry instead. Skip the "References" section (academic reference list, not patient information).
5. **Write output files from Python with `encoding="utf-8"`.** Redirecting console output in PowerShell (`>`) produced broken characters ("HereÆs") even though the text itself was correct.
6. **NIAMS needs a correct URL** for its knee replacement content.

## 4. Chunking (Chunk Size and Overlap)

**Why chunk?**
1. One vector for a whole page mixes many topics and weakens search.
2. **The embedding model has a reading limit:** `all-MiniLM-L6-v2` reads only the first **256 tokens** of a text and **silently drops the rest** (no error).

**Concepts:**
- **Chunk size:** Length of each piece. Too small → context is lost. Too large → topics mix and the token limit is exceeded.
- **Overlap:** Number of words shared by neighbouring chunks, so that a sentence cut at a boundary is complete in at least one chunk.

```text
Text:    [──────────────────────────────────────────]
Chunk 1: [──────────────]
Chunk 2:            [──────────────]     ← overlap
Chunk 3:                       [──────────────]
```

### Experiment 3: Chunk size vs token limit (`06_chunking_experiment.py`)

Clean text: 1,239 words. Model token limit: 256.

| Chunk size | Overlap | Chunks | Longest chunk | Over the limit |
|---|---|---|---|---|
| 100 words | 20 | 16 | 205 tokens | 0 |
| 150 words | 30 | 11 | 274 tokens | 1 |
| 200 words | 40 | 8 | 280 tokens | 1 |
| 400 words | 80 | 4 | 504 tokens | 4 |

- **Exceeding the limit is silent:** With 400-word chunks, all 4 chunks were too long and about half of each was never embedded. The only sign was an easy-to-miss warning: `Token indices sequence length is longer than the specified maximum sequence length for this model (274 > 256)`.
- **About 1.35 tokens per word,** because medical terms are split into several tokens. 256 tokens ≈ 180–190 words, but dense chunks exceeded the limit at 150 words.
- **Overlap works:** the last 30 words of chunk 1 were identical to the first 30 words of chunk 2.
- **Word-based cutting breaks sentences:** chunk 1 ended with "You will not feel any pain during". The overlap kept the full sentence in chunk 2.

### Experiment 4: Three chunking methods (`08b_chunking_methods_compare.py`)

The correct chunk for each question was defined objectively: the chunk that **contains a key sentence** from the page (e.g. "You will not feel any pain during the surgery").

| Question | A) Plain words | B) By section | C) Section + header |
|---|---|---|---|
| Will I feel pain during the surgery? | #2 | **#1** | **#1** |
| Why is knee replacement surgery done? | **#1** | #3 | **#1** |
| What should I do two weeks before surgery? | #6 | **#3** | #4 |
| What is the artificial knee joint made of? | #2 | **#1** | #2 |
| **Recall@1** | 1/4 | **2/4** | **2/4** |
| **Recall@3** | 3/4 | **4/4** | 3/4 |

- A) whole page in ~120-word chunks; B) split by section headings first, heading kept only in metadata; C) like B, with "Knee joint replacement - <Section>:" added to the embedded text.
- **B (section-aware) was best:** the correct chunk was in the top 3 for all four questions. In A, one correct chunk was at rank 6 and would never reach the LLM with K = 3.
- **C (adding a header) gave mixed results:** it fixed the "why" question (#3 → #1) but slightly worsened two others. A likely reason is that the same page title on every chunk makes chunks more similar to each other.

### Decision
- **Split by section headings first, then into ~120-word chunks with 25-word overlap.**
- **Check that every chunk is ≤ 256 tokens** (count with the model's tokenizer). A safer alternative is to size chunks by tokens instead of words.
- **Possible improvements to test on the full question set:** sentence-boundary splitting; a header with the section name only.
- If the embedding model changes, the token limit changes too (`all-mpnet-base-v2`: 384, `multi-qa-MiniLM-L6-cos-v1`: 512); the chunk size must be re-checked.

## 5. Embedding

**Choice:** sentence-transformers library, `all-MiniLM-L6-v2` model (provisional). Candidate: `all-mpnet-base-v2`.

- **Role:** Convert chunks and questions into vectors that carry meaning.
- **Week 1 finding** (`01_embedding_experiment.ipynb`): A passage with almost no words in common with the question got the highest score (0.59); an unrelated sentence scored −0.01; related-but-not-answering passages scored close to the correct one (0.53, 0.51), so the threshold is critical.

### Experiment 5: Three models (`07_embedding_models_experiment.py`)

13 chunks of the MedlinePlus page; 3 answerable and 2 unanswerable questions.
**GAP** = lowest answerable top score − highest unanswerable top score (bigger = easier to set an abstain threshold).

| Model | Description | Vector size | Token limit | Load* | Encode 13 chunks |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 | Current; small, general purpose | 384 | 256 | 3.2 s | 0.24 s |
| multi-qa-MiniLM-L6-cos-v1 | Same size; trained on question → answer pairs | 384 | 512 | 16.3 s | 0.16 s |
| all-mpnet-base-v2 | Larger (~420 MB), general purpose | 768 | 384 | 45.8 s | 1.15 s |

\*Load times include the first download (MiniLM was already cached).

| Model | Lowest answerable | Highest unanswerable | GAP |
|---|---|---|---|
| all-MiniLM-L6-v2 | 0.63 | 0.43 | **0.20** |
| multi-qa-MiniLM-L6-cos-v1 | 0.65 | 0.46 | 0.19 |
| all-mpnet-base-v2 | 0.63 | 0.46 | 0.16 |

### Verification of the retrieved chunks (`07b_check_chunks.py`)

The full top-3 chunks were read for two questions:
- **"Will I feel pain during the surgery?"** — MiniLM put a wrong chunk first (0.63, about pain as a *reason* for surgery) and the correct one second (0.62). mpnet put the correct chunk first (0.72).
- **"Why is knee replacement surgery done?"** — All models were correct. The chunk starts with "The surgery takes about 2 hours" but contains the "Why the Procedure is Performed" section. (Judging a chunk by its first characters was misleading; correctness must be checked on the full text.)

| | Recall@1 | Recall@3 |
|---|---|---|
| all-MiniLM-L6-v2 | 1/2 | 2/2 |
| all-mpnet-base-v2 | 2/2 | 2/2 |

### Findings
1. **A bigger model is not automatically better:** the small model had the largest GAP.
2. **mpnet was more accurate at rank 1** in this small test.
3. **GAP alone is not enough:** a model can return a wrong chunk with a high score. Models must also be compared with **Recall@K** (is the correct chunk in the top K?).
4. **Hard question type:** "How much does knee replacement cost in Turkey?" is on-topic but unanswerable and scored 0.43–0.46 on every model ("What is the capital of France?" ≈ 0). The threshold will probably have to be around 0.50 because of such questions.
5. **The test is small** (one page, five questions); a 0.20 vs 0.19 difference is not meaningful.

### Decision
- **Keep `all-MiniLM-L6-v2` for now** (largest GAP, fastest, correct chunk in the top 3).
- **Evaluate `all-mpnet-base-v2`** on the team's question set; speed is not a problem for 20–40 pages.
- **Final choice:** based on Recall@1, Recall@5 and GAP on the evaluation question set. Each answerable question must record the **URL and section** where its answer is.
- **Language note:** the model is English-only. If Turkish questions are required, a multilingual model (e.g. `paraphrase-multilingual-MiniLM-L12-v2`) is needed, the database must be rebuilt and the threshold re-tuned.
- **Code note:** in the current sentence-transformers version `get_sentence_embedding_dimension()` was renamed to `get_embedding_dimension()`.

## 6. Vector Database

**Choice:** ChromaDB with cosine similarity (provisional; team approval pending).

### Comparison (week 1)

| Feature | ChromaDB | PostgreSQL + pgvector |
|---|---|---|
| Installation | `pip install chromadb` | PostgreSQL server first, then the extension |
| Use from Python | Simple calls (`add`, `query`) | SQL queries, extra connection library |
| Vector search | Yes; stores text and metadata with each vector | Yes; very strong on large data |
| Extra database needed | No | Yes (PostgreSQL) |
| Docker | Runs inside the application, no extra service | Separate PostgreSQL service |
| Strong for | Prototypes, small and medium data | Large multi-user systems, storing other data next to vectors |

**Reasons for ChromaDB:** small data (a few hundred chunks from 20–40 pages); a fast prototype is needed (M2); fewer services make the single `docker-compose up` simpler; it does not block the planned robot interface.
**When to switch to pgvector:** many users or devices, much larger data, or the need to store other data (e.g. chat logs). All database code will live in `src/retrieval/`, so a switch only affects that folder.

### Experiment 6: Real chunks with metadata (`08_chromadb_real_chunks.py`)

- Real MedlinePlus chunks, section-aware chunking, 14 chunks stored in a separate collection (`medlineplus_test`) so the week-1 demo stays intact.
- **Cosine similarity set explicitly** when the collection is created: `metadata={"hnsw:space": "cosine"}`, so similarity = 1 − distance.
- Each search result came back with a ready citation line, e.g.:
  `CITATION: MedlinePlus, "Knee joint replacement", section "Description" - https://medlineplus.gov/ency/article/002974.htm`

### Metadata schema (per chunk)

```text
id                 medlineplus-002974-003   (source + page id + order → stable on re-runs)
url                https://medlineplus.gov/ency/article/002974.htm
title              Knee joint replacement
source             MedlinePlus
section            Why the Procedure is Performed
chunk_in_section   0
(+ from the source registry: date_accessed, last_updated)
```

The database lives in `chroma_db/`, is not pushed to GitHub (`.gitignore`) and can always be rebuilt from the documents.

## 7. Retrieval Parameters

- **Top-K = 5.** Even with the best chunking method, one correct chunk was at rank 3 (and rank 4 with method C); K = 3 is too tight. (The project brief does not fix K.)
- **Threshold:** not decided. Observed so far: answerable questions 0.62–0.72, on-topic unanswerable ("cost in Turkey") 0.43–0.46, off-topic ("capital of France") ≈ 0. The value will be chosen on the evaluation question set and must be re-tuned if the embedding model changes.

## 8. LLM

The project brief requires comparing a **local** and a **hosted** model on the same 200 questions (answer correctness, citation correctness, correct refusals).

### Local model

**Choice:** Ollama + `llama3.2` (3B parameters, ~2 GB).

- **Ollama** runs models on our own computer: free, no internet needed, data stays local. If Ollama asks to create an account, choose "No thanks, I'll use Ollama locally"; an account is free but not needed. Do not use models whose name contains "cloud" (they run on Ollama's servers, not locally).
- **Measured speed:**

| Computer | GPU | Generation speed | Short answer |
|---|---|---|---|
| Old laptop | RTX 3050 Laptop, 4 GB (driver updated 511.65 → 617.14) | ~51 tokens/s | ~3.7 s |
| New laptop | RTX 4060 Laptop, 8 GB (driver 610.60) | ~87–99 tokens/s | ~1.1 s |

- `ollama ps` confirmed **100% GPU** on the new laptop.
- **First call is slow:** on the very first question, prompt evaluation alone took 27 s while the GPU warmed up; later calls took ~1 s. **Warm up the model with one question before a demo.**
- With 8 GB of GPU memory, a larger model (~8B parameters) could be tested later.

### Hosted model

**Status:** not chosen. It will be used through an API; the API key will be stored in `.env` (never pushed to GitHub), with an empty `.env.example` template in the repository. Estimated cost of a 200-question run: a few cents with small models, about 1–2 USD with the strongest models.

## 9. Safety Rule (week 1)

The brief requires medication and emergency questions to be **always** refused with a fixed message.

- Week 1 experiments (`03_rag_experiment.ipynb`) showed that the similarity threshold cannot stop dangerous questions, and that with a medication passage in the database the LLM answered "Can I take ibuprofen…?" from the passage. **The safety check must run before retrieval and the LLM.**
- Current version (v0): keyword list. **Known weakness:** brand names ("Advil"), typos and indirect wording bypass it; the LLM then also stretched the passage ("may be given" → "you can take").
- **Options for later:** a longer list, an embedding-based check against known dangerous questions, an LLM-based classifier, or a combination.
- Observed in the Streamlit demo: the model sometimes adds a passage number to a refusal ("I don't know… [2]"). The prompt should be tightened or the number removed in code.

## 10. Web UI

**Choice:** Streamlit. Web pages written only in Python, with ready-made chat components. The week-1 demo (`04_streamlit_demo.py`) connects the prototype to a chat screen and shows the retrieved passages with their sources. The interface (`app/`) is kept separate from the system logic (`src/`), so another interface (e.g. a robot) can reuse the same logic.

## 11. Containerization

**Choice:** Docker Compose, written at the end of the project. The jury must start everything with one `docker-compose up`. Planned containers: the application (Python, Streamlit, RAG code, ChromaDB) and Ollama. ChromaDB runs inside the application, so no separate database container is needed. Docker files will go in `docker/`.

## 12. Question Language

**Choice:** English (provisional; advisor confirmation pending). The brief does not specify the language; all sources are in English. The jury should be told at the start of the demo that the system works in English.

## 13. Responsible Data Collection

- **Identify ourselves:** a descriptive `User-Agent` on every request ("CiteOrAbstain student project (educational use)").
- **Few, slow requests:** a pause between requests (e.g. 2 s); each page is downloaded **once** and saved in `data/raw/`; later runs use the local copy.
- **Respect robots.txt:** checked per site. NHS allowed our pages. For NIAMS the check failed with an SSL certificate error because Python's `RobotFileParser` does not use the same certificate bundle as `requests`; download robots.txt with `requests` and parse it with `RobotFileParser.parse()`.
- **Terms of use:** raw texts will be stored in the repository. This is fine while the repository is private. Before making it public, each source's terms must be checked (e.g. MedlinePlus encyclopedia pages contain A.D.A.M. content whose republication may be restricted; NHS has its own terms).
- **No real patient data** is ever used (project requirement); only public patient-education pages.

## 14. First Retrieval Prototype (plan for the joint coding day)

```text
URL list (source registry)
   ↓  requests (raw bytes) + trafilatura
Clean text  →  data/raw/                 (downloaded once, saved)
   ↓  split by sections → ~120 words / 25 overlap, ≤ 256 tokens
Chunks + metadata  →  data/processed/chunks.jsonl
   ↓  all-MiniLM-L6-v2
ChromaDB (cosine)  →  chroma_db/          (not in GitHub, can be rebuilt)
   ↓
Question → top 5 chunks + source information
```

| File | Purpose |
|---|---|
| `src/ingestion/extract.py` | URL → clean text, save to `data/raw/`; check final URL, text length, noise lines |
| `src/ingestion/chunk.py` | Text → sections → chunks + metadata; token check |
| `src/retrieval/index.py` | Chunks → vectors → ChromaDB |
| `src/retrieval/search.py` | Question → top 5 chunks + citation |

**Testing:** Recall@5 on the first 20–30 evaluation questions. For unanswerable questions, record the top scores for later threshold tuning. The LLM is not needed this week: the first goal is to retrieve the right document.

The experiment scripts `05`–`09` in `notebooks/` are the first version of this code.

## 15. Future: Robot

The robot would be a new interface: it converts a spoken question to text, sends it to the same RAG system and reads the answer aloud. The chosen technologies do not block this (ChromaDB is light enough for small devices). Important for the robot: keeping the RAG logic independent of the interface, answer speed and language support.

## Experiment Index

| File | Topic | Week |
|---|---|---|
| `01_embedding_experiment.ipynb` | Embeddings and similarity scores | 1 |
| `02_chromadb_experiment.ipynb` | First ChromaDB use (sample sentences) | 1 |
| `03_rag_experiment.ipynb` | First RAG prototype, citation, abstention, safety rule | 1 |
| `04_streamlit_demo.py` | Streamlit chat demo | 1 |
| `05_text_extraction_experiment.py` | BeautifulSoup vs trafilatura | 2 |
| `06_chunking_experiment.py` | Chunk size, overlap, token limit; encoding fix | 2 |
| `07_embedding_models_experiment.py` | Three embedding models, GAP | 2 |
| `07b_check_chunks.py` | Full-text check of retrieved chunks, Recall@K | 2 |
| `08_chromadb_real_chunks.py` | Real chunks + metadata in ChromaDB | 2 |
| `08b_chunking_methods_compare.py` | Three chunking methods, objective ranking | 2 |
| `09_other_sources_test.py` | NHS and NIH NIAMS extraction, robots.txt | 2 |

## Open Questions for the Team / Advisor

1. Approve ChromaDB as the vector database.
2. Confirm English as the question language.
3. Choose the hosted model provider.
4. Approach for the safety rule after the keyword list.
5. Approve the branch + Pull Request rules and adding `requirements-lock.txt`.
6. Find the correct NIAMS knee replacement page; update NHS addresses to `/tests-and-treatments/...`.
7. Check terms of use before making the repository public.
