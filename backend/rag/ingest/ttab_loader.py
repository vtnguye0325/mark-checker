"""
Parse TTAB bulk XML → reasoning-section chunks with metadata.

Filters to ex parte appeals on distinctiveness grounds only.
Extracts the reasoning block; falls back to full decision text if
the heuristic can't locate it.
"""

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from rag.chunker import split_text

_REASONING_START = re.compile(
    r"\b(we find|the board finds|the examining attorney|applicant argues|"
    r"the issue|turning to|we agree|we disagree|analysis)\b",
    re.IGNORECASE,
)
_BOILERPLATE = re.compile(
    r"\b(oral hearing|submitted for decision|appearances|represented by|"
    r"before the board|this case comes up|appeal brief)\b",
    re.IGNORECASE,
)
_EX_PARTE_INDICATORS = re.compile(
    r"\b(ex parte|in re|merely descriptive|primarily merely descriptive|"
    r"section 2\(e\)\(1\)|2\(e\)\(1\)|merely descriptive refusal)\b",
    re.IGNORECASE,
)


def _extract_reasoning(full_text: str) -> str:
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
    reasoning = []
    in_reasoning = False

    for para in paragraphs:
        if _BOILERPLATE.search(para) and not in_reasoning:
            continue
        if _REASONING_START.search(para):
            in_reasoning = True
        if in_reasoning:
            reasoning.append(para)

    if len(reasoning) < 2:
        return full_text

    return "\n\n".join(reasoning)


def _is_ex_parte(text: str) -> bool:
    return bool(_EX_PARTE_INDICATORS.search(text[:2000]))


def _parse_decision(elem: ET.Element) -> dict | None:
    """Extract fields from a single TTAB XML decision element."""
    ns = {"": elem.tag.split("}")[0].lstrip("{") if "}" in elem.tag else ""}

    def find_text(tag: str) -> str:
        node = elem.find(f".//{tag}")
        if node is None and ns.get(""):
            node = elem.find(f".//{{{ns['']}}}tag")
        return (node.text or "").strip() if node is not None else ""

    full_text = find_text("text") or find_text("body") or find_text("content")
    if not full_text or not _is_ex_parte(full_text):
        return None

    mark = find_text("mark") or find_text("markLiteral") or "UNKNOWN"
    nice_class = find_text("internationalClassNumber") or find_text("class") or ""
    serial = find_text("serialNumber") or find_text("serial") or ""
    outcome_raw = (find_text("disposition") or find_text("outcome") or "").lower()
    outcome = "affirmed" if "affirm" in outcome_raw else "reversed" if "revers" in outcome_raw else "unknown"

    reasoning = _extract_reasoning(full_text)
    return {
        "mark": mark,
        "nice_class": nice_class,
        "serial_number": serial,
        "outcome": outcome,
        "reasoning": reasoning,
    }


def load_ttab_chunks(zip_path: str | Path, max_decisions: int | None = None) -> list[dict]:
    """
    Returns chunk dicts ready for ChromaDB upsert.
    max_decisions: cap for partial ingest during development.
    """
    chunks = []
    zip_path = Path(zip_path)
    decision_count = 0

    with zipfile.ZipFile(zip_path) as zf:
        xml_files = [n for n in zf.namelist() if n.lower().endswith(".xml")]
        if not xml_files:
            raise ValueError(f"No XML files found in {zip_path}")

        for filename in xml_files:
            if max_decisions and decision_count >= max_decisions:
                break

            raw = zf.read(filename)
            try:
                root = ET.fromstring(raw)
            except ET.ParseError:
                continue

            for elem in root.iter():
                if max_decisions and decision_count >= max_decisions:
                    break
                local = elem.tag.split("}")[-1].lower()
                if local not in ("decision", "case", "appeal"):
                    continue

                decision = _parse_decision(elem)
                if not decision:
                    continue

                decision_count += 1
                prefix = (
                    f"{decision['mark']} (NC{decision['nice_class']}, "
                    f"{decision['outcome']})"
                )
                full_text = f"{prefix} — {decision['reasoning']}"

                for i, chunk_text in enumerate(split_text(full_text)):
                    chunk_id = f"ttab-{decision['serial_number'] or decision_count}-{i}"
                    chunks.append(
                        {
                            "id": chunk_id,
                            "text": chunk_text,
                            "metadata": {
                                "mark": decision["mark"],
                                "nice_class": decision["nice_class"],
                                "outcome": decision["outcome"],
                                "serial_number": decision["serial_number"],
                                "source": "ttab",
                            },
                        }
                    )

    return chunks


def load_landmark_chunks(json_path: str | Path) -> list[dict]:
    """Load hand-curated landmark cases from JSON."""
    import json

    json_path = Path(json_path)
    if not json_path.exists():
        return []

    with open(json_path) as f:
        cases = json.load(f)

    chunks = []
    for case in cases:
        text = f"{case['mark']} — {case['reasoning']}"
        for i, chunk_text in enumerate(split_text(text)):
            chunk_id = f"landmark-{case.get('citation', case['mark']).replace(' ', '_')}-{i}"
            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "mark": case.get("mark", ""),
                        "citation": case.get("citation", ""),
                        "outcome": case.get("outcome", ""),
                        "nice_class": case.get("nice_class", ""),
                        "source": "court",
                    },
                }
            )

    return chunks
