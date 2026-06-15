"""
Milestone 5: Grounded generation using Groq + ChromaDB retrieval.

ask(question) is the end-to-end RAG function used by app.py:
  1. Retrieve top-k chunks from ChromaDB
  2. Label each chunk with its source filename
  3. Call Groq (llama-3.3-70b-versatile) with a strict grounding prompt
  4. Return answer + deduplicated source list + raw chunks
"""

import os

from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

from embed import EMBEDDING_MODEL, TOP_K, get_collection, retrieve

load_dotenv()

# ── Human-readable labels for source filenames ───────────────────────────────
SOURCE_LABELS = {
    "rmp_olaf_daugulis.txt":    "Rate My Professors — Olafs Daugulis",
    "rmp_crystal_young.txt":    "Rate My Professors — Crystal Young",
    "rmp_mary_bean.txt":        "Rate My Professors — Mary Bean",
    "rmp_robert_comito.txt":    "Rate My Professors — Robert Comito",
    "rmp_bradley_carrow.txt":   "Rate My Professors — Bradley Carrow",
    "rmp_loi_do.txt":           "Rate My Professors — Loi Do",
    "cougargrades_ochem.txt":   "CougarGrades.io — grade distribution data",
    "reddit_uh_ochem.txt":      "Reddit — r/UniversityOfHouston",
    "uh_faculty_chemistry.txt": "UH Chemistry Department — official faculty list",
}

# ── Grounding prompt ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an unofficial guide helping University of Houston students choose \
Organic Chemistry professors (CHEM 2323 and CHEM 2325).

STRICT RULES — follow every one of these:
1. Answer ONLY using information from the context documents provided below.
2. Do NOT draw on training knowledge about professors, grades, or UH — \
even if you believe you know the answer.
3. If the context does not contain enough information to answer, respond \
with exactly: "I don't have enough information in my documents to answer that."
4. Cite sources in your answer using the filename in parentheses, \
e.g. "According to student reviews (rmp_olaf_daugulis.txt)..."
5. Be specific — quote or closely paraphrase what the documents say \
rather than speaking in generalities.\
"""

# ── Module-level singletons — loaded once on first call ─────────────────────
_model: SentenceTransformer | None = None
_collection = None
_groq: Groq | None = None


def _init() -> None:
    global _model, _collection, _groq
    if _model is None:
        print("Loading embedding model...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        _collection = get_collection()
        _groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        print("Ready.")


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        label = SOURCE_LABELS.get(chunk["source"], chunk["source"])
        header = f"[Source: {chunk['source']} — {label}]"
        parts.append(f"{header}\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


# ── Public API ────────────────────────────────────────────────────────────────

def ask(question: str) -> dict:
    """
    Full RAG pipeline: retrieve → prompt → generate.

    Returns:
        answer  (str)        — LLM response grounded in retrieved context
        sources (list[str])  — unique source labels, ordered by retrieval rank
        chunks  (list[dict]) — raw retrieved chunks for debugging
    """
    _init()

    chunks = retrieve(question, _collection, _model, k=TOP_K)
    context = _build_context(chunks)

    completion = _groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Context documents:\n\n{context}"
                    f"\n\nQuestion: {question}"
                ),
            },
        ],
        temperature=0.1,   # low temp keeps answers factual
        max_tokens=600,
    )

    answer = completion.choices[0].message.content.strip()

    # Programmatic source list — deduplicated, ordered by retrieval rank
    seen: set[str] = set()
    sources: list[str] = []
    for chunk in chunks:
        src = chunk["source"]
        if src not in seen:
            seen.add(src)
            label = SOURCE_LABELS.get(src, src)
            sources.append(f"{src}  ({label})")

    return {"answer": answer, "sources": sources, "chunks": chunks}


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    TEST_QUERIES = [
        "How difficult are Olafs Daugulis's exams in Organic Chemistry 1?",
        "What was the average GPA for CHEM 2323 under Crystal Young?",
        "Is Mary Bean still teaching Organic Chemistry at UH?",
        "What is the best pizza place near the engineering quad?",  # out-of-scope test
    ]

    for q in TEST_QUERIES:
        print(f"\n{'=' * 65}")
        print(f"Q: {q}")
        print("-" * 65)
        result = ask(q)
        print(f"A: {result['answer']}")
        print("\nSources:")
        for s in result["sources"]:
            print(f"  • {s}")
