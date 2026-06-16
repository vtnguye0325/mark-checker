"""
Parse a TMEP zip archive (PDF edition) → subsection chunks with metadata.

Expected zip layout (USPTO PDF distribution):
  TMEP/tmep-1200.pdf  ← the file we care about (§§1200–1213 distinctiveness)
  TMEP/tmep-XXXX.pdf  ← other chapters, skipped

Section headers in the PDF appear as lines matching §XXXX or §XXXX.XX.
"""

import io
import re
import zipfile
from pathlib import Path

import pypdf

from rag.chunker import split_text

# Matches body section headers: "1209  Refusal on Basis..." (2-6 spaces, then text)
# Captures paren subsections too: "1209.01(c)  Generic Terms",
# "1209.01(c)(i)  Test for Genericness". Without the (?:\([a-z]+\))* group the
# header has no space after "1209.01" (it's "1209.01(c)") so the line failed to
# match and the whole subsection got swallowed into the flat parent §1209.01.
# TOC lines have 10+ spaces — excluded by the {1,6} bound.
_SECTION_RE = re.compile(r"^(\d{4}(?:\.\d+)?(?:\([a-z]+\))*)\s{1,6}[A-Z\"]")

# Keys must be ordered longest-first so "1209.01(a)" matches before "1209.01" before "1209"
ABERCROMBIE_MAP = {
    "1209.01(a)": "fanciful_arbitrary_suggestive",
    "1209.01(b)": "merely_descriptive",
    "1209.01(c)": "generic",
    "1209.01": "distinctiveness_continuum",
    "1209": "merely_descriptive",
    "1211": "surname",
    "1212": "acquired_distinctiveness",
    "1213": "disclaimer",
}

_TARGET_PDFS = {"tmep-1200.pdf"}


def _abercrombie_tier(section_number: str) -> str:
    for key, tier in ABERCROMBIE_MAP.items():
        if section_number.startswith(key):
            return tier
    return "general"


def _is_relevant_section(section_number: str) -> bool:
    try:
        top = int(section_number.split(".")[0])
        return 1200 <= top <= 1213
    except ValueError:
        return False


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text(extraction_mode="layout")
        if text:
            pages.append(text)
    return "\n".join(pages)


def _split_into_subsections(text: str) -> list[dict]:
    """Split raw text at section header boundaries → list of {section, title, body}."""
    lines = text.splitlines()
    subsections = []
    current_section: str | None = None
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        m = _SECTION_RE.match(line.strip())
        if m:
            if current_section and _is_relevant_section(current_section):
                subsections.append(
                    {
                        "section": current_section,
                        "title": current_title.strip(),
                        "body": "\n".join(current_lines).strip(),
                    }
                )
            current_section = m.group(1)
            current_title = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_section and _is_relevant_section(current_section):
        subsections.append(
            {
                "section": current_section,
                "title": current_title.strip(),
                "body": "\n".join(current_lines).strip(),
            }
        )

    return subsections


def load_tmep_chunks(zip_path: str | Path) -> list[dict]:
    """
    Returns chunk dicts ready for ChromaDB upsert:
      id, text, metadata {section_number, section_title, abercrombie_tier, source}
    """
    chunks = []
    zip_path = Path(zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        pdf_files = [
            n for n in zf.namelist()
            if n.lower().endswith(".pdf") and Path(n).name in _TARGET_PDFS
        ]
        if not pdf_files:
            raise ValueError(
                f"Could not find {_TARGET_PDFS} in {zip_path}. "
                f"Files present: {[n for n in zf.namelist() if n.endswith('.pdf')]}"
            )

        for filename in pdf_files:
            print(f"  Parsing {filename} ...")
            raw = zf.read(filename)
            text = _extract_pdf_text(raw)
            subsections = _split_into_subsections(text)
            print(f"  Found {len(subsections)} subsections")

            for sub in subsections:
                if not sub["body"]:
                    continue
                full_text = f"TMEP §{sub['section']} — {sub['title']}\n\n{sub['body']}"
                for i, chunk_text in enumerate(split_text(full_text)):
                    chunk_id = f"tmep-{sub['section']}-{i}"
                    chunks.append(
                        {
                            "id": chunk_id,
                            "text": chunk_text,
                            "metadata": {
                                "section_number": sub["section"],
                                "section_title": sub["title"],
                                "abercrombie_tier": _abercrombie_tier(sub["section"]),
                                "source": "tmep",
                            },
                        }
                    )

    return chunks
