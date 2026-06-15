"""
Milestone 3: Document ingestion and chunking pipeline.

Loads all .txt files from documents/, cleans them, splits into chunks,
and prints a diagnostic report. Run this before embedding (Milestone 4).

Chunk spec (from planning.md):
  - chunk_size  = 300 tokens  (~1200 chars at 4 chars/token)
  - chunk_overlap = 50 tokens (~200 chars)
  - Splitter: RecursiveCharacterTextSplitter
"""

import re
import random
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCUMENTS_DIR = Path("documents")

# Character approximations of the token targets in planning.md
CHUNK_SIZE = 1200     # ~300 tokens
CHUNK_OVERLAP = 200   # ~50 tokens


# ---------------------------------------------------------------------------
# Stage 1: Load
# ---------------------------------------------------------------------------

def load_documents(docs_dir: Path) -> list[dict]:
    docs = []
    for path in sorted(docs_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        docs.append({"source": path.name, "text": text})
        print(f"  Loaded: {path.name} ({len(text):,} chars)")
    return docs


# ---------------------------------------------------------------------------
# Stage 2: Clean
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    # HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Common HTML entities
    entities = {
        "&amp;": "&", "&nbsp;": " ", "&lt;": "<", "&gt;": ">",
        "&#39;": "'", "&quot;": '"', "&apos;": "'", "&hellip;": "...",
    }
    for entity, replacement in entities.items():
        text = text.replace(entity, replacement)
    # Collapse horizontal whitespace (tabs, multiple spaces) but keep newlines
    text = re.sub(r"[ \t]+", " ", text)
    # Strip trailing space from each line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    # Collapse more than two consecutive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Stage 3: Chunk
# ---------------------------------------------------------------------------

def chunk_documents(docs: list[dict]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        # Try to split on paragraph → sentence → word boundaries in that order
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in docs:
        splits = splitter.split_text(doc["text"])
        for i, split in enumerate(splits):
            stripped = split.strip()
            if stripped:  # skip empty chunks
                chunks.append({
                    "source": doc["source"],
                    "chunk_index": i,
                    "text": stripped,
                })
    return chunks


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def print_sample_chunks(chunks: list[dict], n: int = 5) -> None:
    sample = random.sample(chunks, min(n, len(chunks)))
    for i, chunk in enumerate(sample, 1):
        preview = chunk["text"][:300].replace("\n", " ")
        print(f"[Chunk {i}]")
        print(f"  source      : {chunk['source']}")
        print(f"  chunk_index : {chunk['chunk_index']}")
        print(f"  length      : {len(chunk['text'])} chars")
        print(f"  text        : {preview}")
        print()


def run_diagnostics(chunks: list[dict]) -> None:
    total = len(chunks)
    avg_len = sum(len(c["text"]) for c in chunks) / total if total else 0
    empty = sum(1 for c in chunks if not c["text"].strip())
    html_artifacts = sum(1 for c in chunks if re.search(r"<[a-z]+[\s>/]", c["text"]))

    print(f"  Total chunks    : {total}")
    print(f"  Avg chunk length: {avg_len:.0f} chars (~{avg_len / 4:.0f} tokens)")

    if total < 50:
        print("  WARNING: Fewer than 50 chunks — add more documents or reduce chunk size.")
    elif total > 2000:
        print("  WARNING: More than 2000 chunks — consider increasing chunk size.")
    else:
        print(f"  Chunk count is in the healthy range (50–2000).")

    if empty:
        print(f"  WARNING: {empty} empty chunk(s) found — check your source documents.")
    if html_artifacts:
        print(f"  WARNING: {html_artifacts} chunk(s) may still contain HTML tags.")

    # Per-source breakdown
    sources: dict[str, int] = {}
    for c in chunks:
        sources[c["source"]] = sources.get(c["source"], 0) + 1
    print("\n  Chunks per source:")
    for src, count in sorted(sources.items()):
        print(f"    {src}: {count}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("  Milestone 3 — Document Ingestion Pipeline")
    print("=" * 55)

    # 1. Load
    print("\n[1] Loading documents...")
    docs = load_documents(DOCUMENTS_DIR)
    if not docs:
        print("  No .txt files found in documents/. Add your source files and re-run.")
        return
    print(f"  {len(docs)} document(s) loaded.\n")

    # 2. Clean
    print("[2] Cleaning documents...")
    for doc in docs:
        before = len(doc["text"])
        doc["text"] = clean_text(doc["text"])
        after = len(doc["text"])
        print(f"  {doc['source']}: {before:,} → {after:,} chars")
    print()

    # 3. Inspect one cleaned document
    print("[3] Sample cleaned document (first 600 chars of first file):")
    print("-" * 55)
    print(docs[0]["text"][:600])
    print("-" * 55)
    print()

    # 4. Chunk
    print("[4] Chunking documents...")
    chunks = chunk_documents(docs)
    print(f"  {len(chunks)} chunk(s) produced.\n")

    if not chunks:
        print("  No chunks produced. Make sure your document files contain real text.")
        return

    # 5. Sample chunks
    print("[5] Five representative chunks (random sample):")
    print("-" * 55)
    print_sample_chunks(chunks, n=5)

    # 6. Diagnostics
    print("[6] Diagnostics:")
    run_diagnostics(chunks)
    print()
    print("Done. Fix any warnings above before moving to Milestone 4.")


if __name__ == "__main__":
    main()
