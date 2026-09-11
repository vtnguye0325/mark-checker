# scripts/

Developer scripts. Run every one from the repository root, with the backend
virtualenv active and the `mark-checker` package installed:

```bash
source backend/.venv/bin/activate
pip install --no-deps -e backend
```

| Script | What it does | What it needs |
| --- | --- | --- |
| `build_rag_index.py` | Builds or rebuilds the ChromaDB index from the TMEP, TTAB, and Lanham Act sources. `--reset` wipes the collections first. | The source archives under `backend/mark_checker/rag/data/`, the embedding model (`torch`), and disk space for the ChromaDB directory. |
| `eval_rag_retrieval.py` | Scores the index. The default run embeds probe queries and checks that each expected TMEP section reaches the top 5. `--spot` runs the full model-to-agent pipeline and prints the retrieved doctrine. | A built index. `--spot` also needs the trained model (`torch`) and `DEEPSEEK_API_KEY`. |
| `smoke_test.py` | Classifies the cases in the `CASES` list and reports each label against the expected one. Edit the list to add a case. | The trained model under `backend/model/` and `torch`. |
| `test-ci.sh` | Runs the checks that CI runs: ruff over `backend/`, the unit tests, and the frontend build. Creates `backend/.venv` when it is absent. | `python3`, `npm`, and network access on the first run. |

`backend/scripts/docker_download_model.py` is not a developer script. The
Docker build runs it to pull the model repo named by `HF_MODEL_ID` into
`MODEL_DIR`.
