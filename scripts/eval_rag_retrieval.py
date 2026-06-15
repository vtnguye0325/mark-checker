"""
Quick retrieval eval for the ChromaDB RAG index.

Tests section reachability and spot-checks relevance without needing
the HyDE LLM call (embeds query text directly).

Usage:
    python scripts/eval_rag_retrieval.py
    python scripts/eval_rag_retrieval.py --query "software for organizing files"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.embedder import embed_query
from backend.rag.store import get_tmep_collection, get_ttab_collection

N_RESULTS = 5


def query_tmep(text: str, n: int = N_RESULTS) -> list[dict]:
    col = get_tmep_collection()
    emb = embed_query(text)
    results = col.query(query_embeddings=[emb], n_results=n)
    return [
        {
            "section": results["metadatas"][0][i]["section_number"],
            "title": results["metadatas"][0][i]["section_title"],
            "tier": results["metadatas"][0][i]["abercrombie_tier"],
            "text": results["documents"][0][i][:120],
            "distance": results["distances"][0][i],
        }
        for i in range(len(results["documents"][0]))
    ]


def query_ttab(text: str, n: int = 3) -> list[dict]:
    col = get_ttab_collection()
    emb = embed_query(text)
    results = col.query(query_embeddings=[emb], n_results=n)
    return [
        {
            "mark": results["metadatas"][0][i].get("mark", ""),
            "source": results["metadatas"][0][i].get("source", ""),
            "outcome": results["metadatas"][0][i].get("outcome", ""),
            "text": results["documents"][0][i][:120],
            "distance": results["distances"][0][i],
        }
        for i in range(len(results["documents"][0]))
    ]


def print_results(label: str, results: list[dict]) -> None:
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    for r in results:
        dist = r["distance"]
        if "section" in r:
            print(f"  §{r['section']} [{r['tier']}]  dist={dist:.3f}")
            print(f"    {r['title'][:70]}")
        else:
            print(f"  {r['mark']} ({r['source']}, {r['outcome']})  dist={dist:.3f}")
        print(f"    \"{r['text'].strip()[:100]}...\"")


# ---------------------------------------------------------------------------
# Section reachability probes — each query should surface the named section
# ---------------------------------------------------------------------------
# expected_prefix: any returned section that STARTS WITH this string is a hit
REACHABILITY_PROBES = [
    {
        "label": "§1209 — merely descriptive",
        "query": "Refusal under section 2(e)(1) on the basis of mere descriptiveness. "
                 "The mark merely describes an ingredient quality or function of the goods. "
                 "The examining attorney issued a merely descriptive refusal.",
        "expected_prefix": "1209",
    },
    {
        "label": "§1209.01(a) — fanciful / arbitrary / suggestive",
        "query": "The mark is a coined invented word with no prior meaning requiring "
                 "imagination to connect it to the goods. It is fanciful arbitrary or suggestive "
                 "and therefore inherently distinctive.",
        "expected_prefix": "1209.01",
    },
    {
        "label": "§1209.01(c) — generic",
        "query": "The term is generic and can never acquire trademark significance. "
                 "Genericness refusal: the primary significance test shows consumers use "
                 "the term to refer to the genus or category of goods not the source.",
        "expected_prefix": "1209.01(c)",
    },
    {
        "label": "§1211 — surname",
        "query": "The mark is primarily merely a surname. The primary significance of "
                 "the mark to the purchasing public is as a surname.",
        "expected_prefix": "1211",
    },
    {
        "label": "§1212 — acquired distinctiveness / secondary meaning",
        "query": "The mark has acquired distinctiveness through long and exclusive use. "
                 "Secondary meaning has been established by consumer recognition.",
        "expected_prefix": "1212",
    },
]

# ---------------------------------------------------------------------------
# Spot-check marks with known expected outcomes
# ---------------------------------------------------------------------------
SPOT_CHECKS = [
    {
        "mark": "CHARCOAL TOOTHPASTE",
        "description": "Toothpaste made with activated charcoal for whitening",
        "nice_class": "3",
        "expected_section_prefix": "1209",  # merely descriptive refusal
    },
    {
        "mark": "KODAK",
        "description": "Coined word for cameras and photographic equipment",
        "nice_class": "9",
        "expected_section_prefix": "1209.01",  # fanciful — inherently distinctive
    },
    {
        "mark": "APPLE",
        "description": "Computers and consumer electronics",
        "nice_class": "9",
        "expected_section_prefix": "1209.01",  # arbitrary — inherently distinctive
    },
    {
        "mark": "SPEEDY MUFFLER",
        "description": "Automobile muffler repair services",
        "nice_class": "37",
        "expected_section_prefix": "1209.01",  # suggestive
    },
]


def _section_matches(section: str, prefix: str) -> bool:
    return section == prefix or section.startswith(prefix + ".") or section.startswith(prefix + "(")


def run_reachability() -> tuple[int, int]:
    print("\n=== SECTION REACHABILITY ===")
    passed = 0
    for probe in REACHABILITY_PROBES:
        results = query_tmep(probe["query"])
        prefix = probe["expected_prefix"]
        hit = any(_section_matches(r["section"], prefix) for r in results)
        status = "PASS" if hit else "FAIL"
        if hit:
            passed += 1
        print(f"\n[{status}] {probe['label']}")
        for r in results[:3]:
            marker = "  ✓" if _section_matches(r["section"], prefix) else "   "
            print(f"{marker} §{r['section']} [{r['tier']}]  dist={r['distance']:.3f}  {r['title'][:55]}")
    return passed, len(REACHABILITY_PROBES)


def run_spot_checks() -> None:
    print("\n\n=== SPOT CHECKS (mark → expected section family in top-3) ===")
    for check in SPOT_CHECKS:
        query = (
            f"Trademark distinctiveness analysis for {check['mark']}: "
            f"{check['description']} (NICE class {check['nice_class']})"
        )
        results = query_tmep(query, n=3)
        prefix = check["expected_section_prefix"]
        hit = any(_section_matches(r["section"], prefix) for r in results)
        status = "PASS" if hit else "MISS"
        print(f"\n[{status}] {check['mark']}  (expect §{prefix})")
        for r in results:
            marker = "  ✓" if _section_matches(r["section"], prefix) else "   "
            print(f"{marker} §{r['section']} [{r['tier']}]  dist={r['distance']:.3f}")


def run_custom_query(query: str) -> None:
    print(f"\n=== CUSTOM QUERY ===\n  \"{query}\"")
    print_results("TMEP results", query_tmep(query))
    print_results("TTAB / landmark results", query_ttab(query))


def print_collection_stats() -> None:
    tmep = get_tmep_collection()
    ttab = get_ttab_collection()
    print(f"\n=== COLLECTION STATS ===")
    print(f"  tmep collection: {tmep.count()} docs")
    print(f"  ttab collection: {ttab.count()} docs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="Run a single custom query against both collections")
    parser.add_argument("--spot", action="store_true", help="Run spot checks only")
    parser.add_argument("--reach", action="store_true", help="Run reachability probes only")
    args = parser.parse_args()

    print_collection_stats()

    if args.query:
        run_custom_query(args.query)
        return

    if args.spot:
        run_spot_checks()
        return

    if args.reach:
        passed, total = run_reachability()
        print(f"\nReachability: {passed}/{total} sections reachable in top-5")
        return

    # Default: run everything
    passed, total = run_reachability()
    run_spot_checks()
    print(f"\n{'═'*60}")
    print(f"  Reachability: {passed}/{total} key sections surfaced in top-5")
    print(f"{'═'*60}")


if __name__ == "__main__":
    main()
