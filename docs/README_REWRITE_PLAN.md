# Implementation Plan — Rewrite the Top-Level README

**Goal:** Replace the current 583-line operations manual with a short, high-level README that
tells a reader what the app does and why it is hard.

**Primary audience:** A recruiter or a hiring engineer who opens the repo for 60 seconds.

**Do not start work until the plan is approved.**

---

## 1. Audience assumptions

The recruiter reader has these traits. Every decision in this plan follows from them.

| Trait | Consequence for the README |
|---|---|
| Skims. Reads the top 30 lines, then scrolls. | Put the strongest content first. No directory tree at the top. |
| Does not know trademark law. | Explain the Abercrombie spectrum in one plain sentence. |
| Does not know ModernBERT, ChromaDB, or TTAB. | Name each term once, then say what it does in plain words. |
| Wants proof of engineering judgment, not command lists. | Show the decisions and the trade-offs. Move commands to `docs/`. |
| May be non-technical (a sourcer). | The first two paragraphs must work with zero technical vocabulary. |

**Design rule:** The README answers *what*, *why*, and *what was hard*. The `docs/` files answer *how*.

---

## 2. Current state

- `README.md` is 25 KB and 583+ lines.
- It opens with a 65-line directory tree.
- 21 of 25 headings cover setup: Docker, Cloudflare Tunnel, RAG index builds, API reference,
  tests, CI, and input format.
- It never states who uses the app or what problem the app solves.

**Verdict:** The content is good, but the file is the wrong document for this audience. The plan
moves the content, it does not delete the content.

---

## 3. Phases

### Phase 1 — Gather the facts (read only)

Produce a scratch notes file. Write no README content yet.

1. Run `graphify query` against `graphify-out/graph.json` for:
   - the end-to-end request flow,
   - the role of the RAG layer,
   - the contract of `/predict`, `/explain`, and `/analyze`.
2. Read `frontend/src/hooks/useTrademarkPipeline.js` to find the real user journey.
   This file drives `predict -> explain -> analyze`. It defines what the user sees.
3. Read `backend/app/routes/*.py` for the input shape and the output shape only.
4. Read `backend/rag/agent.py` and `backend/rag/retriever.py` to state the retrieval strategy
   in one sentence.
5. Read `docs/PLAN.md` for the product intent behind the RAG work.
6. Read `tests/test_model_predictions.py` for the regression-test count and the accuracy claim.
7. Run `git log --oneline | wc -l` and check `.github/workflows/` for the CI and deploy story.

**Exit test:** You can answer these five questions in one sentence each.
- What does a user type in?
- What does the user get back?
- Why is a fine-tuned model better here than a prompt to a general LLM?
- What does the RAG layer add that the classifier cannot give?
- What is the hardest engineering problem in the repo?

### Phase 2 — Find the numbers

A recruiter README needs concrete figures. Collect the real values. Never estimate.

- Model accuracy, or the regression-test pass count if no held-out metric exists.
- Training-set size.
- Count of indexed doctrine chunks in ChromaDB.
- Median latency for each of the three endpoints.
- Test count and coverage.

**Rule:** If a number cannot be verified, leave the number out. Do not write a number you did
not measure.

### Phase 3 — Split the content

Move the operational sections out of `README.md`. Create these files:

| New file | Content moved from README |
|---|---|
| `docs/DEPLOYMENT.md` | Docker, Cloudflare Tunnel, the security checklist, troubleshooting |
| `docs/API.md` | `GET /health`, `POST /predict`, `POST /explain`, `POST /analyze`, input format, rate limits |
| `docs/RAG.md` | ChromaDB setup, index builds, TMEP and TTAB ingest, retrieval eval |
| `docs/DEVELOPMENT.md` | Requirements, local run, tests, smoke test, CI/CD, project structure tree |

**Rule:** Move the text verbatim. Do not rewrite it in this phase. A move and a rewrite in one
step hides mistakes.

### Phase 4 — Write the new README

Target: 90 to 130 lines. This structure, in this order.

1. **Title and one-line hook** — What the app does, in under 20 words.
2. **Live demo and screenshot** — A link and one image. This is the highest-value block for a
   recruiter. Place the image above the fold.
3. **The problem** (2 short paragraphs) — Trademark law grades a name on the Abercrombie
   spectrum, from generic to fanciful. That grade decides whether the name is registrable.
   The judgment is subjective, slow, and expensive. Write this with no jargon.
4. **What the app does** — A worked example. One mark in, the verdict, the confidence, the
   words that drove the verdict, and the doctrine that supports the verdict.
5. **How it works** — 5 numbered steps, one line each. Add one diagram
   (Mermaid, or an SVG). No code in this section.
6. **Engineering highlights** — 4 to 6 bullets. This section carries the interview signal.
   Each bullet states a decision and the reason for the decision. Candidates:
   - Fine-tuned ModernBERT instead of a prompt to a general LLM, and the reason.
   - The RAG layer grounds the analysis in TMEP and TTAB, so the LLM cites doctrine
     instead of inventing doctrine.
   - A tool-calling agent writes targeted doctrine queries instead of one flat similarity search.
   - Feature attribution shows which words drove the verdict, so the output is auditable.
   - A 50-case regression suite catches model drift.
   - Rate limiting, Turnstile, and a Cloudflare Tunnel for a safe public deployment.
7. **Tech stack** — A compact table. Layer, choice, one-line reason.
8. **Documentation** — A link table to the four `docs/` files.
9. **Quick start** — 3 commands, maximum. Link to `docs/DEPLOYMENT.md` for the rest.
10. **Status and limits** — One honest paragraph. State what the app does not do. This reads
    as maturity, not as weakness.

### Phase 5 — Add the visuals

- Capture a screenshot of the result screen. Store it at `docs/assets/`.
- Draw the pipeline diagram with Mermaid, so the diagram renders on GitHub with no build step.
- Keep the total image weight under 1 MB.

### Phase 6 — Verify

- Check every link resolves. Check every moved section arrived in its new file.
- Run each Quick Start command on a clean checkout.
- Read the first 30 lines aloud. A non-technical reader must understand the app from those lines.
- Confirm no unverified number survived from Phase 2.
- Confirm the file is under 150 lines.

---

## 4. Writing rules

- Active voice. Name the agent.
- One instruction, one sentence. 20 words or less.
- Define each domain term at its first use: Abercrombie spectrum, TMEP, TTAB, distinctiveness.
- No emoji headers. No badge wall. At most 3 badges.
- Every claim about quality carries a number or a link to the code.
- State the trade-off next to each decision. A recruiter reads the trade-off as the signal.

---

## 5. Deliverables

- `README.md` — rewritten, under 150 lines.
- `docs/DEPLOYMENT.md`, `docs/API.md`, `docs/RAG.md`, `docs/DEVELOPMENT.md` — new.
- `docs/assets/` — screenshot and diagram source.
- One commit per phase, so each step stays reviewable.

---

## 6. Open questions

Answer these before Phase 4 starts.

1. Is a live demo URL available? If yes, the URL goes in the top block.
2. Does a held-out accuracy figure exist, or does only the 50-case regression suite exist?
3. Should the README name the author and link to a portfolio or LinkedIn?
4. Is the repo public now, or does it become public later?
