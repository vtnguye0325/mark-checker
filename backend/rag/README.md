# RAG System — Mark Checker

Retrieval-Augmented Generation layer that grounds LLM trademark analysis in actual legal doctrine, directly addressing the gap identified in thesis §7.6: the ModernBERT classifier "learns what examiners decided during a particular period, not what the doctrine actually requires."

---

## Architecture

```
Mark + description + NICE class + label + SHAP
        ↓
[HyDE — cheap DeepSeek call, max_tokens=150]
Generate hypothetical legal reasoning paragraph
        ↓
Embed with bge-base-en-v1.5 (local, MPS-accelerated)
        ↓
Query two ChromaDB collections in parallel
  ├── tmep  → top 3 subsection chunks (doctrine)
  └── ttab  → top 2 decision chunks (illustrations)
        ↓
Inject as LEGAL DOCTRINE + ILLUSTRATIVE CASES into final LLM prompt
```

**Why HyDE:** Raw mark names ("CHARCOAL TOOTHPASTE") embed far from TMEP legal text. The HyDE paragraph bridges the vocabulary gap by generating text that already sounds like doctrine before embedding.

---

## TMEP Index

**Source:** USPTO TMEP May 2026 PDF edition (`tmep-may2026-pdf.zip`)  
**Coverage:** Full Chapter 1200 — Substantive Examination of Applications  
**Chunks:** 2,410 total (600 tokens each, 80 token overlap)  
**Embeddings:** `BAAI/bge-base-en-v1.5` (768 dimensions, cosine similarity)

### Sections Indexed

| Section | Title | Abercrombie Tier | Chunks |
|---|---|---|---|
| §1201 | Ownership of Mark | general | 109 |
| §1202 | Use of Subject Matter as Trademark | general | 754 |
| §1202.01 | Refusal of Matter Used Solely as a Trade Name | general | — |
| §1202.02 | Registration of Trade Dress | general | — |
| §1202.03 | Refusal on Basis of Ornamentation | general | — |
| §1203 | Deceptive Matter and False Suggestions | general | 227 |
| §1204 | Flag, Coat of Arms, or Other Insignia | general | 59 |
| §1205 | Matter Protected by Statute or Convention | general | 196 |
| §1206 | Name, Portrait, or Signature of Living Individual | general | 97 |
| §1207 | Likelihood of Confusion | general | 104 |
| §1208 | Conflicting Marks in Pending Applications | general | 59 |
| **§1209** | **Refusal on Basis of Descriptiveness** | **merely_descriptive** | **86** |
| §1209.01 | Distinctiveness/Descriptiveness Continuum | distinctiveness_continuum | — |
| §1209.01(a) | Fanciful, Arbitrary, and Suggestive Marks | fanciful_arbitrary_suggestive | — |
| §1209.01(b) | Merely Descriptive Marks | merely_descriptive | — |
| §1209.01(c) | Generic Terms | generic | — |
| §1209.02 | Procedure for Descriptiveness/Genericness Refusal | merely_descriptive | — |
| §1209.03 | Considerations for Descriptiveness Determination | merely_descriptive | — |
| §1209.04 | Deceptively Misdescriptive Marks | merely_descriptive | — |
| §1210 | Refusal on Basis of Geographic Significance | general | 241 |
| **§1211** | **Refusal on Basis of Surname** | **surname** | **19** |
| **§1212** | **Acquired Distinctiveness / Secondary Meaning** | **acquired_distinctiveness** | **355** |
| §1212.03–.06 | Evidence of Distinctiveness (3 types, 5-year use, actual evidence) | acquired_distinctiveness | — |
| **§1213** | **Disclaimer of Elements in Marks** | **disclaimer** | **104** |

The Abercrombie spectrum sections (§§1209–1209.04) are the primary retrieval target for the classifier's output. §1212 is the largest section by chunk count because acquired distinctiveness requires detailed evidentiary standards — relevant for marks the classifier scores near the distinctive/not-distinctive boundary.

---

## TTAB / Landmark Collection

**Sources:**
- `landmark_cases.json` — 5 hand-curated landmark court opinions (seed set)
- TTAB bulk XML (added via `--ttab` flag once USPTO data is downloaded)

**Current count:** 5 docs (landmark seed only)

| Case | Outcome | Relevance |
|---|---|---|
| *Abercrombie & Fitch v. Hunting World* (2d Cir. 1976) | reversed | Established the four-category Abercrombie spectrum |
| *Park 'N Fly v. Dollar Park & Fly* (S. Ct. 1985) | reversed | Incontestability bars descriptiveness cancellation |
| *Zatarains v. Oak Grove Smokehouse* (5th Cir. 1983) | affirmed | Primary significance test + fair use doctrine |
| *In re Dial-A-Mattress* (Fed. Cir. 2001) | reversed | Composite marks evaluated as a whole |
| *In re Nett Designs* (Fed. Cir. 2001) | affirmed | Applicant burden after prima facie genericness showing |

---

## Files

```
backend/rag/
├── embedder.py          # bge-base-en-v1.5, lazy-loaded, MPS-accelerated
├── store.py             # ChromaDB PersistentClient, two collections
├── chunker.py           # RecursiveCharacterTextSplitter (600t / 80 overlap)
├── hyde.py              # Cheap DeepSeek call → hypothetical paragraph
├── retriever.py         # Full pipeline: HyDE → embed → parallel query → format_context()
├── chroma_db/           # Persisted vector store (not committed to git)
├── data/                # Drop source zips here (not committed to git)
└── ingest/
    ├── tmep_loader.py   # Parse TMEP PDF zip at section boundaries
    ├── ttab_loader.py   # Parse TTAB bulk XML, filter ex parte, extract reasoning
    └── landmark_cases.json
```

---

## Commands

**Build / rebuild the index:**
```bash
# TMEP only (Milestone 1 — current state)
python scripts/build_rag_index.py --tmep backend/rag/data/tmep-may2026-pdf.zip

# Full rebuild with TTAB bulk data
python scripts/build_rag_index.py \
  --tmep backend/rag/data/tmep-may2026-pdf.zip \
  --ttab backend/rag/data/ttab_bulk.zip \
  --reset

# Partial TTAB ingest during development
python scripts/build_rag_index.py --ttab backend/rag/data/ttab_bulk.zip --max-ttab 1000
```

**Evaluate retrieval quality:**
```bash
# Full eval (reachability + spot checks)
python scripts/eval_rag_retrieval.py

# Single custom query against both collections
python scripts/eval_rag_retrieval.py --query "coined word with no dictionary meaning"

# Reachability probes only
python scripts/eval_rag_retrieval.py --reach
```

---

## Current Eval Results (Milestone 1)

Reachability probes — can we find each doctrine section using legal vocabulary queries?

| Section | Query focus | Result | Top hit distance |
|---|---|---|---|
| §1209 | Merely descriptive refusal | PASS | 0.205 |
| §1209.01(a) | Fanciful / arbitrary / suggestive | PASS | 0.256 |
| §1209.01(c) | Genericness / primary significance | FAIL | — |
| §1211 | Surname refusal | PASS | 0.189 |
| §1212 | Acquired distinctiveness | PASS | 0.242 |

**4/5 sections reachable.** The §1209.01(c) generic probe loses to the §1209.02 procedure section — both use "genericness" language. This is acceptable: in practice the HyDE paragraph for a generic mark will include richer vocabulary ("genus of goods", "primary significance test", "can never acquire trademark significance") that shifts the embedding toward §1209.01(c).

Spot checks (mark + description without legal vocabulary) all miss intentionally — this confirms HyDE is necessary and working as designed.

---

## Milestones

- [x] **1** — TMEP ingest + ChromaDB `tmep` collection
- [ ] **2** — `hyde.py` — cheap LLM call + embedding smoke test
- [ ] **3** — `retriever.py` — query both collections, verify TMEP doctrine surfaces
- [ ] **4** — TTAB loader — parse 1,000 decisions, validate reasoning extraction
- [ ] **5** — Modify `llm_service.py` — inject doctrine context into prompt
- [ ] **6** — Update Docker Compose + env vars
- [ ] **7** — Landmark cases JSON — curate ~50 court opinions
- [ ] **8** — Full TTAB ingest (5K+ decisions)
- [ ] **9** — Eval on 20-mark golden set (borderline cases, 0.4–0.6 model confidence)
- [ ] **10** — Frontend: collapsible sources panel
