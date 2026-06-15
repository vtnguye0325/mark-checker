"""
Build (or rebuild) the RAG ChromaDB index.

Usage:
  python scripts/build_rag_index.py --tmep backend/rag/data/tmep_2026.zip
  python scripts/build_rag_index.py --tmep backend/rag/data/tmep_2026.zip \
                                     --ttab backend/rag/data/ttab_bulk.zip \
                                     --max-ttab 1000
  python scripts/build_rag_index.py --reset   # wipe and rebuild from scratch
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.store import get_tmep_collection, get_ttab_collection, reset_collections
from backend.rag.embedder import embed_documents
from backend.rag.ingest.tmep_loader import load_tmep_chunks
from backend.rag.ingest.ttab_loader import load_ttab_chunks, load_landmark_chunks

LANDMARK_JSON = Path(__file__).parent.parent / "backend/rag/ingest/landmark_cases.json"
BATCH_SIZE = 64


def upsert_chunks(collection, chunks: list[dict]) -> None:
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        embeddings = embed_documents(texts)
        collection.upsert(
            ids=[c["id"] for c in batch],
            documents=texts,
            embeddings=embeddings,
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  upserted {start + len(batch)}/{len(chunks)}", end="\r")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build RAG ChromaDB index")
    parser.add_argument("--tmep", type=Path, help="Path to TMEP zip archive")
    parser.add_argument("--ttab", type=Path, help="Path to TTAB bulk XML zip")
    parser.add_argument("--max-ttab", type=int, default=None, help="Cap TTAB decisions (dev)")
    parser.add_argument("--reset", action="store_true", help="Wipe collections before ingest")
    args = parser.parse_args()

    if args.reset:
        print("Resetting collections...")
        reset_collections()

    if args.tmep:
        print(f"Loading TMEP from {args.tmep} ...")
        chunks = load_tmep_chunks(args.tmep)
        print(f"  {len(chunks)} chunks extracted")
        col = get_tmep_collection()
        upsert_chunks(col, chunks)
        print(f"TMEP done — {col.count()} total docs in collection")

    print(f"Loading landmark cases from {LANDMARK_JSON} ...")
    landmark_chunks = load_landmark_chunks(LANDMARK_JSON)
    if landmark_chunks:
        col = get_ttab_collection()
        upsert_chunks(col, landmark_chunks)
        print(f"Landmark cases done — {col.count()} total docs in TTAB collection")

    if args.ttab:
        print(f"Loading TTAB from {args.ttab} (max={args.max_ttab}) ...")
        chunks = load_ttab_chunks(args.ttab, max_decisions=args.max_ttab)
        print(f"  {len(chunks)} chunks extracted")
        col = get_ttab_collection()
        upsert_chunks(col, chunks)
        print(f"TTAB done — {col.count()} total docs in collection")

    if not args.tmep and not args.ttab:
        print("Nothing to ingest. Pass --tmep and/or --ttab.")
        parser.print_help()


if __name__ == "__main__":
    main()
