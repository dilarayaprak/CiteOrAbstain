# CiteOrAbstain

A question-answering assistant for knee replacement patients. It answers **only** from trusted public health documents and **cites its sources**. When the answer is not in the documents, or the question is about medication or an emergency, it **abstains** and says: *"I don't know, please consult your healthcare team."*

Graduation project — Applied NLP (RAG). Advisor: Assoc. Prof. Dr. Semih Yumuşak

## How it works

1. **Document collection:** Short passages from public patient-education pages (MedlinePlus, NIH NIAMS, NHS) with source links.
2. **Retrieval:** A vector database finds the passages most similar to the question.
3. **Answer or abstain:** If the similarity score is above a threshold, the LLM answers with citations. Otherwise the assistant abstains. Medication and emergency questions are always refused.
4. **Web chat and evaluation:** Streamlit interface and an evaluation script for the 200-question test set.

Technology choices and their reasons: [docs/technology_decisions.md](docs/technology_decisions.md)

**Türkçe, adım adım ve açıklamalı kurulum rehberi:** [docs/kurulum_rehberi.md](docs/kurulum_rehberi.md)

## Project structure

```text
app/            Streamlit web interface
data/raw/       Collected source documents
data/processed/ Chunked passages
docs/           Requirements, architecture, technology decisions
evaluation/     Test questions and evaluation script
literature/     Literature review
notebooks/      Experiments
src/ingestion/  Document loading and chunking
src/retrieval/  Embedding and vector search
src/generation/ Threshold, LLM answer, citation, abstention
tests/          Tests
docker/         Docker files
```

## Before you start (one time only)

1. **GitHub account:** Create one at https://github.com/signup if you don't have it, and accept the repository invitation sent to your email.
2. **Install Python 3.12 and Git:**

```powershell
winget install Python.Python.3.12
winget install Git.Git
```

3. **Close all PowerShell windows and open a new one.** Check the installation:

```powershell
py -3.12 --version
git --version
```

4. **Tell Git who you are** (use the same email as your GitHub account, so your commits appear under your name):

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
git config --global init.defaultBranch main
git config --global core.autocrlf true
```

## Setup (first time)

Keep the project outside OneDrive-synced folders (Desktop, Documents). We use `C:\Users\<you>\Projects`:

```powershell
cd $HOME
mkdir Projects
cd Projects
git clone https://github.com/dilarayaprak/CiteOrAbstain.git
cd CiteOrAbstain
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Local LLM setup (Ollama)

If your computer has an NVIDIA graphics card, update its driver first (https://www.nvidia.com/Download/index.aspx). With an old driver the model runs on the CPU and is much slower. You can check your card and driver with `nvidia-smi`.

1. Install Ollama: `winget install Ollama.Ollama` (or download from https://ollama.com/download). When asked to sign up, choose **"No thanks, I'll use Ollama locally"**.
2. Close **all** PowerShell windows and open a new one, then check: `ollama --version`
3. Download the model (about 2 GB): `ollama pull llama3.2`
4. Test it: `ollama run llama3.2` (type `/bye` to exit)

## Every time you start working

```powershell
cd $HOME\Projects\CiteOrAbstain
.\venv\Scripts\Activate.ps1
git pull
```

Check that the line starts with `(venv)` before installing packages or running code.

## Sending your work to GitHub

Always in this order: **add → commit → push**

```powershell
git status
git add path/to/your_file
git commit -m "Short description of what you did"
git push
```

Your changes stay only on your computer until you push. Others' changes reach your computer only when you run `git pull`.

## Running the experiments

- **Notebooks:** `python -m notebook`, then open the files in `notebooks/`
- **Streamlit chat demo:** `python -m streamlit run notebooks/04_streamlit_demo.py`

The experiments need Ollama running and the sample passages created by `02_chromadb_experiment.ipynb` (run it first on a new computer).

## Troubleshooting (Windows)

- **"running scripts is disabled"** when activating venv: run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
- **"Authentication failed"** when cloning or pushing: run `git credential-manager github login`, then try again.
- Always use `python -m pip` instead of `pip`. Some antivirus programs block the venv's `pip.exe`.
- **A newly installed program is "not recognized"** (for example `ollama`): close **all** PowerShell windows and open a new one.
- **Push is rejected and Git asks you to pull first:** someone else pushed changes. Run `git pull`, then `git push` again.

## Team

- Selenay — Requirements and system architecture
- Göksu — Literature review and evaluation
- Dilara Yaprak — Technical infrastructure and technology decisions
