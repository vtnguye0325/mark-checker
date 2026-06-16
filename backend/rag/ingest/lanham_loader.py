"""
Parse tmlaw.pdf (USPTO "U.S. Trademark Law — Rules of Practice & Federal Statutes", Jan 1 2026)
→ section-level chunks for the statute ChromaDB collection.

Structure:
  pp. 1-220: 37 CFR Trademark Rules of Practice (Parts 2, 7, 11, etc.)
  pp. 221-296: Lanham Act / 15 U.S.C. federal statutes

Header formats in the PDF body (no leading whitespace — TOC lines are indented 8+):
  CFR:     § 2.35  Adding, deleting, or substituting bases.
  Statute: § 1 (15 U.S.C. §                               1051).  Application for...
"""

from __future__ import annotations

import re
from pathlib import Path

import pypdf

from rag.chunker import split_text

# CFR body headers: "§ 2.35  Title."
# Requires 2+ spaces between section number and title to exclude cross-refs
# like "§ 2.45(a)(4)(i)(C); however..." which have no space gap.
_CFR_RE = re.compile(r"^§ (\d+\.\d+)\s{2,}(.+)$")

# Statute body headers: "§ 1 (15 U.S.C. §                               1051).  Title"
# \s* handles whitespace corruption in USC citation numbers.
# \)?\.? — closing paren and period both optional (§16A/§16B truncated-line edge cases).
_STATUTE_RE = re.compile(r"^§ (\d+[A-Z]?)\s+\(15 U\.S\.C\. §\s*(\d+[a-z]*)\)?\.?\s*(.*)")


def _sanitize_id(s: str) -> str:
    return re.sub(r"[^\w-]", "_", s)


def _extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    reader = pypdf.PdfReader(str(pdf_path))
    return [
        (i, page.extract_text(extraction_mode="layout") or "")
        for i, page in enumerate(reader.pages)
    ]


def _parse_sections(pages: list[tuple[int, str]]) -> list[dict]:
    """Split text at heading boundaries → list of section dicts."""
    sections: list[dict] = []
    current: dict | None = None

    for page_idx, text in pages:
        for line in text.splitlines():
            # Body headers have no leading whitespace; TOC lines are indented 8+.
            if not line.startswith("§"):
                if current is not None:
                    current["lines"].append(line)
                continue

            stripped = line.rstrip()

            # Statute header takes priority (more specific pattern)
            m = _STATUTE_RE.match(stripped)
            if m:
                if current is not None:
                    sections.append(current)
                lanham_sec = m.group(1)
                usc_num = m.group(2)
                title = m.group(3).strip().rstrip(".")
                current = {
                    "section": lanham_sec,
                    "title": title,
                    "citation": f"15 U.S.C. § {usc_num}",
                    "doc_type": "statute",
                    "page": page_idx,
                    "lines": [],
                }
                continue

            m = _CFR_RE.match(stripped)
            if m:
                if current is not None:
                    sections.append(current)
                cfr_sec = m.group(1)
                title = m.group(2).strip().rstrip(".")
                current = {
                    "section": cfr_sec,
                    "title": title,
                    "citation": f"37 CFR § {cfr_sec}",
                    "doc_type": "cfr_rule",
                    "page": page_idx,
                    "lines": [],
                }
                continue

            # Non-header line starting with § (cross-ref in body text)
            if current is not None:
                current["lines"].append(line)

    if current is not None:
        sections.append(current)

    return sections


def load_lanham_chunks(pdf_path: str | Path) -> list[dict]:
    """
    Returns chunk dicts ready for ChromaDB upsert:
      id, text, metadata {doc_type, section_number, section_title, citation, source, page}
    """
    pdf_path = Path(pdf_path)
    pages = _extract_pages(pdf_path)
    sections = _parse_sections(pages)
    n_cfr = sum(1 for s in sections if s["doc_type"] == "cfr_rule")
    n_statute = sum(1 for s in sections if s["doc_type"] == "statute")
    print(f"  Found {len(sections)} sections ({n_cfr} CFR, {n_statute} statute)")

    chunks = []
    for sec in sections:
        body = "\n".join(sec["lines"]).strip()
        if not body:
            continue
        full_text = f"{sec['citation']} — {sec['title']}\n\n{body}"
        for i, chunk_text in enumerate(split_text(full_text)):
            chunk_id = f"statute-{_sanitize_id(sec['section'])}-{i}"
            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "doc_type": sec["doc_type"],
                        "section_number": sec["section"],
                        "section_title": sec["title"],
                        "citation": sec["citation"],
                        "source": "statute",
                        "page": sec["page"],
                    },
                }
            )

    return chunks
