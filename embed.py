"""
Milestone 4: Embed chunks into ChromaDB and test retrieval.

Reads chunks from the ingest pipeline, embeds them with all-MiniLM-L6-v2,
stores them in a persistent ChromaDB collection, then tests retrieval
against the evaluation queries from planning.md.

Run:
    venv/bin/python embed.py          # (re)build the vector store + run tests
    venv/bin/python embed.py --test   # test retrieval only (skip rebuild)
"""

import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import DOCUMENTS_DIR, chunk_documents, clean_text, load_documents

# ── Config ──────────────────────────────────────────────────────────────────
CHROMA_DIR       = Path("chroma_db")
COLLECTION_NAME  = "uh_ochem"
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"
TOP_K            = 8
EMBED_BATCH_SIZE = 64

# Evaluation queries from planning.md
EVAL_QUERIES = [
    "How difficult are Olafs Daugulis's exams in Organic Chemistry 1?",
    "What was the average GPA for CHEM 2323 under Crystal Young?",
    "Is Robert Comito or Bradley Carrow better for OChem 2?",
    "Is Mary Bean still teaching Organic Chemistry at UH?",
    "Is attendance required for Olaf Daugulis's OChem lectures?",
]


# ── Vector store helpers ─────────────────────────────────────────────────────

def build_vectorstore(chunks: list[dict], model: SentenceTransformer) -> chromadb.Collection:
    """Embed all chunks and write them to a fresh ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Always rebuild so the store stays in sync with the documents folder
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  Deleted existing collection.")
    except Exception:
        pass

    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # cosine distance for sentence embeddings
    )

    texts     = [c["text"]        for c in chunks]
    ids       = [f"{c['source']}__{c['chunk_index']}" for c in chunks]
    metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]

    print(f"  Embedding {len(texts)} chunks (batch size {EMBED_BATCH_SIZE})...")
    embeddings = model.encode(
        texts,
        batch_size=EMBED_BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )
    print(f"  ChromaDB now holds {collection.count()} chunks.")
    return collection


def get_collection() -> chromadb.Collection:
    """Open the existing persistent collection (for use in generation scripts)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(COLLECTION_NAME)


# ── Public retrieval function ────────────────────────────────────────────────

def retrieve(
    query: str,
    collection: chromadb.Collection,
    model: SentenceTransformer,
    k: int = TOP_K,
) -> list[dict]:
    """
    Embed a query string and return the top-k most similar chunks.

    Returns a list of dicts with keys:
        text, source, chunk_index, distance
    Distance is cosine distance in [0, 2]; lower = more similar.
    """
    query_embedding = model.encode([query], convert_to_numpy=True).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    output = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "text":        text,
            "source":      meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance":    dist,
        })
    return output


# ── Retrieval test ────────────────────────────────────────────────────────────

def run_retrieval_tests(collection: chromadb.Collection, model: SentenceTransformer) -> None:
    print(f"\n{'=' * 60}")
    print(f"  Retrieval tests — top-k={TOP_K}, distance metric=cosine")
    print(f"  (distance < 0.3 = strong match | 0.3–0.5 = decent | > 0.5 = weak)")
    print(f"{'=' * 60}")

    for query in EVAL_QUERIES[:3]:   # test first 3 eval queries
        print(f"\nQuery: {query}")
        print("-" * 60)
        results = retrieve(query, collection, model, k=TOP_K)
        for i, r in enumerate(results, 1):
            preview = r["text"][:280].replace("\n", " ")
            flag = " ⚠ weak" if r["distance"] > 0.5 else ""
            print(f"  [{i}] dist={r['distance']:.3f}{flag} | {r['source']}")
            print(f"       {preview}")
            print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    test_only = "--test" in sys.argv

    print("=" * 60)
    print("  Milestone 4 — Embedding + Retrieval")
    print("=" * 60)

    print(f"\n[1] Loading embedding model ({EMBEDDING_MODEL})...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("  Model loaded.")

    if test_only:
        print("\n[--test mode] Skipping rebuild, opening existing collection...")
        collection = get_collection()
        print(f"  Collection has {collection.count()} chunks.")
    else:
        print("\n[2] Loading and chunking documents...")
        docs = load_documents(DOCUMENTS_DIR)
        for doc in docs:
            doc["text"] = clean_text(doc["text"])
        chunks = chunk_documents(docs)
        print(f"  {len(chunks)} chunks ready.\n")

        print("[3] Building vector store...")
        collection = build_vectorstore(chunks, model)

    run_retrieval_tests(collection, model)

    print("\nDone.")
    if not test_only:
        print("If distances are below 0.5 and results look relevant, commit and move to Milestone 5.")


if __name__ == "__main__":
    main()
