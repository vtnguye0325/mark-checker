"""
Quick smoke test — edit CASES below and run:

    python trademark_app/scripts/smoke_test.py
    python trademark_app/scripts/smoke_test.py --verbose

Each case is (formatted_input, expected_label).
formatted_input is the full dot-separated bert_input_processed string.
expected_label is 'distinctive' or 'not_distinctive'.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.model_service import predict_one

# ---------------------------------------------------------------------------
# Edit this list to test the cases you care about.
# ---------------------------------------------------------------------------
CASES: list[tuple[str, str]] = [
    (
        "APPLE. computers and consumer electronics. no translation required."
        " mark present in Wordnet. mark length is 1. NICE category is 9."
        " scientific research navigation surveying photographic cinematographic"
        " audiovisual optical weighing measuring signalling detecting testing"
        " inspecting lifesaving and teaching apparatus and instruments apparatus"
        " and instruments for conducting switching transforming accumulating"
        " regulating or controlling the distribution or use of electricity"
        " apparatus and instruments for recording transmitting reproducing or"
        " processing sound images or data recorded and downloadable media"
        " computer software blank digital or analogue recording and storage media"
        " mechanisms for coinoperated apparatus cash registers calculating devices"
        " computers and computer peripheral devices diving suits divers masks ear"
        " plugs for divers nose clips for divers and swimmers gloves for divers"
        " breathing apparatus for underwater swimming fireextinguishing apparatus."
        " no Pseudo mark",
        "distinctive",
    ),
    # Add more cases here — copy the format above.
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print(f"=== Smoke Test ({len(CASES)} case{'s' if len(CASES) != 1 else ''}) ===\n")
    passed = failed = 0

    for i, (text, expected) in enumerate(CASES, 1):
        result = predict_one(text)
        label = result["label"]
        status = "PASS" if label == expected else "FAIL"

        if label == expected:
            passed += 1
        else:
            failed += 1

        mark = text.split(". ")[0]
        print(f"[{status}] #{i:02d}  {mark}")
        print(f"       Expected          : {expected}")
        print(f"       Got               : {label}")
        print(f"       p_distinctive     : {result['prob_distinctive']:.4f}")
        print(f"       p_not_distinctive : {result['prob_not_distinctive']:.4f}")

        if args.verbose:
            print("       --- verbose ---")
            for j, field in enumerate(text.split(". ")):
                print(f"         [{j}] {field}")
            print(f"       Raw result  : {result}")

        print()

    print(f"Results: {passed} passed, {failed} failed out of {len(CASES)} cases")


if __name__ == "__main__":
    main()
