Put each evaluation under a dated folder, for example:

`artifacts/2026-04-12_forward_only/`

- `METADATA.txt` — paste the exact `play.py` command and container name (created by the helper script).
- `metrics_training_last.json` — optional; from `scripts/export_training_metrics.py` on your training run’s `events.out.tfevents.*`.
- `videos/` — copy of `rl-video-step-0.mp4` (not committed by default; see root `.gitignore`).

To commit a short clip anyway, use **Git LFS** or host the video on Drive / S3 and link it in your report.
