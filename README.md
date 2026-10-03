\# CiteOrAbstain



A question-answering assistant for knee replacement patients. It answers \*\*only\*\* from trusted public health documents and \*\*cites its sources\*\*. When the answer is not in the documents, or the question is about medication or an emergency, it \*\*abstains\*\* and says: \*"I don't know, please consult your healthcare team."\*



Graduation project — Applied NLP (RAG). Advisor: Assoc. Prof. Dr. Semih Yumuşak



\## How it works



1\. \*\*Document collection:\*\* Short passages from public patient-education pages (MedlinePlus, NIH NIAMS, NHS) with source links.

2\. \*\*Retrieval:\*\* A vector database finds the passages most similar to the question.

3\. \*\*Answer or abstain:\*\* If the similarity score is above a threshold, the LLM answers with citations. Otherwise the assistant abstains. Medication and emergency questions are always refused.

4\. \*\*Web chat and evaluation:\*\* Streamlit interface and an evaluation script for the 200-question test set.



\## Project structure



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



\## Setup (first time)



Requirements: \*\*Python 3.12\*\* and \*\*Git\*\*



```powershell

git clone https://github.com/dilarayaprak/CiteOrAbstain.git

cd CiteOrAbstain

py -3.12 -m venv venv

.\\venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip

python -m pip install -r requirements.txt

```



\## Every time you start working



```powershell

cd $HOME\\Projects\\CiteOrAbstain

.\\venv\\Scripts\\Activate.ps1

git pull

```



Check that the line starts with `(venv)` before installing packages or running code.



\## Troubleshooting (Windows)



\- \*\*"running scripts is disabled"\*\* when activating venv:

&#x20; `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

\- \*\*"Authentication failed"\*\* when cloning or pushing:

&#x20; `git credential-manager github login`, then try again.

\- Always use `python -m pip` instead of `pip`. Some antivirus programs block the venv's `pip.exe`.



\## Team



\- Selenay — Requirements and system architecture

\- Göksu — Literature review and evaluation

\- Dilara Yaprak — Technical infrastructure and technology decisions

