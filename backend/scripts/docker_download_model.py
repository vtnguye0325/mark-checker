"""Download a Hugging Face model repo into MODEL_DIR (used at Docker image build time)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from huggingface_hub import snapshot_download


def main() -> None:
    repo_id = os.environ.get("HF_MODEL_ID", "").strip()
    if not repo_id:
        print("ERROR: HF_MODEL_ID environment variable is required at build time.", file=sys.stderr)
        sys.exit(1)

    out_dir = os.environ.get("MODEL_DIR", "/opt/model").strip()
    token = os.environ.get("HF_TOKEN") or None
    if token == "":
        token = None

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        local_dir=out_dir,
        token=token,
    )
    print(f"Downloaded {repo_id!r} to {out_dir!r}")


if __name__ == "__main__":
    main()
