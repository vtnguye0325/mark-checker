# RAG System Plan — Mark Checker

> All decisions below confirmed via grill-me session (2026-06-14).
> Context: this system extends Vy Nguyen's MS thesis (May 2026) which identifies in §7.6
> that the ModernBERT model "learns what examiners decided during a particular period,
> not what the doctrine actually requires." The RAG system directly addresses that gap.

---

## Current Architecture

```
User input → ModernBERT classifier → SHAP attributions → DeepSeek LLM (bare prompt) → Analysis text
```

The LLM has no grounding in legal doctrine — it reasons from examiner-behavior patterns
absorbed by the model. The RAG layer adds doctrine retrieval so the LLM reasons from
what trademark law *requires*, not what examiners *did*.

---

## Target Architecture

```
Mark + description + NICE class + label + SHAP attributions
        ↓
[LLM Call 1 — cheap/fast DeepSeek]
Generate hypothetical legal reasoning paragraph (HyDE)
        ↓
Embed HyDE paragraph → query two separate vector collections in parallel
        ├── TMEP collection  → top 3 subsection chunks
        └── TTAB collection  → top 2 reasoning-section chunks
        ↓
Assemble context: TMEP doctrine (first) + TTAB illustrations (second)
        ↓
[LLM Call 2 — full DeepSeek]
Analysis with grounded doctrine context + SHAP attributions
        ↓
Analysis text shown to user
```

**Why two separate LLM calls:** HyDE paragraph is a retrieval artifact only — does not
need to be high quality, just legally-vocabulary-rich enough to embed well against TMEP.
Small/fast call keeps total latency reasonable.

**Why not use prob_distinctive for routing:** The ModernBERT model is heavily skewed
toward class 1 (89.7% distinctive base rate, 99% recall on majority class). Confidence
tiers would route almost every mark to the same doctrine bucket. The RAG layer is
intentionally independent of the model's probability output.

---

## Design Decision: Doctrine Retrieval (Design B)

The RAG retrieves **what the law requires**, not **what examiners did**:

- **Primary source**: TMEP sections — canonical rules per Abercrombie tier
- **Secondary source**: TTAB ex parte appeal decisions — illustrative examples of doctrine applied
- **NOT used**: USPTO filing outcomes, training dataset, examiner behavior statistics

This directly closes the gap named in thesis §7.6.

---

## Knowledge Base

### Source 1 — TMEP (Primary Doctrine)

- **Download**: Zipped full-text from `uspto.gov/trademarks/guides-and-manuals/tmep-archives`
  (May 2026 edition, no login required)
- **Chunking**: Subsection level (~400–700 tokens each)
  - Each subsection = one coherent legal concept (e.g. §1202.01 Fanciful Marks)
  - Metadata: `section_number`, `section_title`, `abercrombie_tier`
  - Discard procedural appendices, keep §§1200–1213 (distinctiveness doctrine)
- **Target**: ~200–300 chunks covering the full Abercrombie spectrum

Key sections to index:
- §1202.01 — Fanciful marks
- §1202.02 — Arbitrary marks
- §1202.03 — Suggestive marks
- §1209 — Merely descriptive marks
- §1209.01 — Primary meaning test
- §1211 — Generic marks
- §1212 — Acquired distinctiveness / secondary meaning
- §1213 — Disclaimer requirements

### Source 2 — TTAB Ex Parte Decisions (Illustrative)

- **Download**: USPTO Open Data Portal at `data.uspto.gov/bulkdata`
  *(Requires USPTO.gov account login as of June 18, 2026)*
- **Filter**: Ex parte appeals only (applicant vs. examiner on distinctiveness grounds)
  — NOT inter partes proceedings (likelihood of confusion between parties)
- **Chunking**: Extract reasoning section only — discard procedural header, appearances,
  boilerplate legal standard recitation, and one-sentence holding
  - Reasoning section typically 300–800 tokens per decision
  - Metadata: `mark`, `nice_class`, `outcome` (affirmed/reversed), `serial_number`
- **Target**: ~5,000–10,000 decisions

### Source 3 — Landmark Court Opinions (Curated)

- ~50 hand-curated cases that shaped Abercrombie doctrine
  (*Abercrombie & Fitch v. Hunting World*, *Park 'N Fly*, *Zatarain's*,
  *Dial-A-Mattress*, *In re Nett Designs*, etc.)
- Extract reasoning paragraphs, store as TTAB collection with `source: "court"`

---

## Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| Vector store | **ChromaDB** (local, file-persisted) | Zero infra, runs in Docker, two named collections |
| Embeddings | **`text-embedding-3-small`** (OpenAI) | Fast, cheap (<$0.001/1K tokens), same API ecosystem |
| HyDE model | **`deepseek-chat`** (low max_tokens=150) | Fast cheap call; output only needs to be embedable |
| Analysis model | **`deepseek-chat`** (full, max_tokens=700) | Existing LLM service, unchanged |
| Chunking | **LangChain `RecursiveCharacterTextSplitter`** | Handles legal text well |

---

## HyDE Prompt Inputs

The cheap LLM call receives (does NOT use `prob_distinctive`):

```
mark:          {mark}
description:   {description}
nice_class:    {nice_class} — {nice_class_description}
label:         {label}  (distinctive | not_distinctive)
attributions:  {shap_attributions_block}
```

Output: a 3–4 sentence hypothetical legal reasoning paragraph using Abercrombie
vocabulary. This paragraph is embedded and used as the retrieval query vector.

---

## Implementation Plan

### Directory Structure

```
backend/rag/
├── __init__.py
├── ingest/
│   ├── tmep_loader.py          # parse TMEP zip → subsection chunks
│   ├── ttab_loader.py          # parse TTAB bulk data → reasoning extraction
│   └── landmark_cases.json     # hand-curated ~50 court opinions
├── chunker.py                  # text splitting + metadata tagging
├── embedder.py                 # wraps text-embedding-3-small
├── store.py                    # ChromaDB: two collections (tmep, ttab)
├── hyde.py                     # cheap LLM call → hypothetical paragraph
└── retriever.py                # embed HyDE → query both collections → merge
```

### Phase 1 — Data Pipeline

1. `scripts/build_rag_index.py` — orchestrates full ingest, idempotent upserts
2. TMEP loader: parse HTML/text from zip, split at `§XXXX.XX` boundaries
3. TTAB loader: parse bulk XML, filter ex parte, extract reasoning block
4. Landmark cases: load from JSON, treat as TTAB collection entries

### Phase 2 — Retrieval Service

**`backend/rag/retriever.py`**

```python
def retrieve(mark, description, nice_class, label, attributions) -> dict:
    hypothesis = generate_hyde_paragraph(mark, description, nice_class, label, attributions)
    embedding = embed(hypothesis)
    tmep_chunks = tmep_collection.query(embedding, n_results=3)
    ttab_chunks = ttab_collection.query(embedding, n_results=2)
    return {"tmep": tmep_chunks, "ttab": ttab_chunks}
```

### Phase 3 — LLM Integration

Modify `backend/app/services/llm_service.py`:

- `analyze_trademark()` calls `retrieve()` first, then builds the prompt
- Prompt gains a `LEGAL DOCTRINE` section (TMEP chunks) followed by
  `ILLUSTRATIVE CASES` section (TTAB chunks), injected before the four output sections
- LLM instruction: "Ground your analysis in the doctrine above. When citing a case,
  reference it by mark name."

Format in prompt:
```
LEGAL DOCTRINE:
[1] TMEP §1209 — A mark is merely descriptive if it describes an ingredient,
    quality, characteristic, function, feature, purpose, or use...
[2] TMEP §1202.03 — A suggestive mark requires imagination, thought, or perception
    to reach a conclusion about the nature of the goods...

ILLUSTRATIVE CASES:
[3] PARTYBALLOONS (NC28, affirmed non-distinctive) — The board held the compound
    directly described a product category without requiring imagination...
```

### Phase 4 — API & Frontend

- `AnalyzeResponse` gains optional `sources: list[str]` field
- Frontend `LLMAnalysis.jsx`: collapsible "Legal sources" panel
- Low priority — analysis quality is the main win

### Phase 5 — Eval

- 20-mark golden set focused on borderline cases (0.4–0.6 model confidence) —
  the zone where §7.3 of the thesis says the triage workflow defers to humans
  and where doctrine grounding adds the most value
- Compare RAG vs. no-RAG on legal accuracy (do cited sections actually apply?)
- Tune `n_results` split (3+2) based on results

---

## Docker / Infra Changes

```yaml
volumes:
  - ./backend/rag/chroma_db:/app/rag/chroma_db

environment:
  - OPENAI_API_KEY=...       # for text-embedding-3-small
  - RAG_TMEP_N_RESULTS=3
  - RAG_TTAB_N_RESULTS=2
```

No new containers — ChromaDB runs in-process.

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| TTAB bulk data requires USPTO login (June 2026) | Create account; script auth once |
| HyDE paragraph quality varies | HyDE only needs to be embedable, not perfect; eval retrieval precision on golden set |
| TMEP subsection boundaries irregular | Regex on `§XXXX` pattern + manual review of edge cases |
| Two LLM calls doubles latency | HyDE call capped at max_tokens=150; target <1s for HyDE, <5s total |
| TTAB reasoning extraction misses section | Fallback: use full decision text if heuristic fails to find reasoning block |

---

## Milestone Order

1. [ ] TMEP ingest + ChromaDB `tmep` collection — validates pipeline end-to-end
2. [ ] `hyde.py` — cheap LLM call + embedding smoke test
3. [ ] `retriever.py` — query both collections, verify TMEP doctrine surfaces correctly
4. [ ] TTAB loader — parse 1,000 decisions, validate reasoning extraction
5. [ ] Modify `llm_service.py` — inject doctrine context into prompt
6. [ ] Update Docker compose + env vars
7. [ ] Landmark cases JSON — curate ~50 court opinions
8. [ ] Full TTAB ingest (5K+ decisions)
9. [ ] Eval on 20-mark golden set (borderline cases)
10. [ ] Frontend: collapsible sources panel
