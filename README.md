# Isaac Lab experiments (eval + reports)

Small **host-side** helpers around Isaac Lab in Docker:

| Item | Purpose |
|------|--------|
| `docs/FIRST_EVAL_RUN.md` | Step-by-step first eval + git |
| `scripts/play_and_collect.sh` | `docker exec` → `play.py` with `--video` → copy `videos/play` to `artifacts/` |
| `scripts/export_training_metrics.py` | Last TensorBoard scalars → JSON |

Training code and checkpoints stay in **Isaac Lab** / your container; this repo holds **protocol, scripts, and small artifacts** (metadata + metrics JSON).

## Quick start

See **`docs/FIRST_EVAL_RUN.md`**.
