"""CiteOrAbstain - Streamlit mini demo (experiment).

Run from the project root:
    python -m streamlit run notebooks/04_streamlit_demo.py

Uses the sample passages stored in chroma_db by the earlier experiments.
This is a learning prototype, not the final application.
"""

import re
from pathlib import Path

import chromadb
import ollama
import streamlit as st
from sentence_transformers import SentenceTransformer

# chroma_db lives in the project root (one level above notebooks/)
DB_PATH = Path(__file__).resolve().parent.parent / "chroma_db"

MEDICATION_KEYWORDS = [
    "ibuprofen", "paracetamol", "acetaminophen", "aspirin", "painkiller", "painkillers",
    "medication", "medications", "medicine", "drug", "drugs", "dose", "dosage",
    "pill", "pills", "tablet", "tablets", "mg", "antibiotic", "antibiotics", "blood thinner",
]

EMERGENCY_KEYWORDS = [
    "emergency", "chest pain", "can't breathe", "cannot breathe",
    "heavy bleeding", "unconscious", "fainted",
]

SAFETY_MESSAGE = (
    "I can't answer questions about medications or emergencies. "
    "Please consult your healthcare team. "
    "In an emergency, call emergency services immediately."
)


@st.cache_resource
def load_resources():
    """Load the embedding model and the ChromaDB collection only once."""
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection(name="knee_passages")
    return model, collection


def is_unsafe(question):
    q = question.lower()
    for keyword in MEDICATION_KEYWORDS + EMERGENCY_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", q):
            return True
    return False


def answer(question, k=3):
    # 0) Safety check BEFORE retrieval and LLM
    if is_unsafe(question):
        return SAFETY_MESSAGE, []

    model, collection = load_resources()

    # 1) Retrieval
    results = collection.query(
        query_embeddings=[model.encode(question).tolist()],
        n_results=k,
    )
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    # 2) Augmentation
    context = ""
    for i, (doc, meta) in enumerate(zip(docs, metas), start=1):
        context += f"[{i}] ({meta['source']}) {doc}\n"

    prompt = f"""Answer the question using ONLY the passages below.
After your answer, write the number of the passage you used, like [1].
If the passages do not contain the answer, reply exactly:
"I don't know, please consult your healthcare team."

Passages:
{context}
Question: {question}
Answer:"""

    # 3) Generation
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"], list(zip(docs, metas))


# ---------------- Web interface ----------------

st.title("CiteOrAbstain (demo)")
st.caption("Experimental prototype using sample passages. Not medical advice.")

# Keep the chat history while the page is open
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("Ask a question about knee replacement")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the documents..."):
            text, sources = answer(question)
        st.write(text)
        if sources:
            with st.expander("Retrieved passages"):
                for i, (doc, meta) in enumerate(sources, start=1):
                    st.write(f"[{i}] **{meta['source']}**: {doc}")

    st.session_state.messages.append({"role": "assistant", "content": text})
