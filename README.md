# Isaac Lab experiments (eval + reports)

**Author:** [MariamDundua](https://github.com/MariamDundua) on GitHub.

After you create the remote repo, connect it with:

```bash
git remote add origin https://github.com/MariamDundua/isaac-lab-experiments.git
git push -u origin main
```

Small **host-side** helpers around Isaac Lab in Docker:

| Item | Purpose |
|------|--------|
| `docs/FIRST_EVAL_RUN.md` | Step-by-step first eval + git |
| `scripts/play_and_collect.sh` | `docker exec` → `play.py` with `--video` → copy `videos/play` to `artifacts/` |
| `scripts/export_training_metrics.py` | Last TensorBoard scalars → JSON |
| `docs/STRESS_TEST.md` | What counts as a stress test + copy-paste commands |
| `scripts/stress_test_play.sh` | Several play+video runs with different command ranges |

Training code and checkpoints stay in **Isaac Lab** / your container; this repo holds **protocol, scripts, and small artifacts** (metadata + metrics JSON).

## Quick start

See **`docs/FIRST_EVAL_RUN.md`**.
