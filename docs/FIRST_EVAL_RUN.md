# First evaluation run — step by step

Goal: one **documented** eval (play + video) plus **training metrics** in JSON, all under `artifacts/`, with **scripts** committed to git.

## Prerequisites

- Docker container named **`vscode`** (or set `ISAAC_CONTAINER`).
- Isaac Lab at **`/workspace/isaaclab`** in the container.
- A trained checkpoint path **inside the container**, e.g.  
  `logs/rsl_rl/unitree_go2_rough/2026-04-12_18-11-57/model_1499.pt`.

## Step 1 — Sync code (if you edited configs on the host)

Push your task configs into the container (your usual workflow), e.g. `docker cp` or `isaaclab_workflow_helpers.py sync-configs`.

## Step 2 — Export **training** metrics (from TensorBoard event file)

On the **host**, point at the **training run directory** that contains `events.out.tfevents.*`.

If the run only exists in the container, copy it once:

```bash
docker cp vscode:/workspace/isaaclab/logs/rsl_rl/unitree_go2_rough/2026-04-12_18-11-57 ./tb_training_run
```

Then:

```bash
cd /path/to/isaac-lab-experiments
pip3 install -r requirements.txt   # tensorboard for export_training_metrics.py
python3 scripts/export_training_metrics.py ./tb_training_run -o artifacts/MY_FIRST_REPORT/metrics_training_last.json
```

Commit the JSON (small) with git.

## Step 3 — Run **play** + **video** and collect files

From the **repo root**:

```bash
chmod +x scripts/play_and_collect.sh
export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/2026-04-12_18-11-57/model_1499.pt"
export ARTIFACT_NAME="MY_FIRST_REPORT"
./scripts/play_and_collect.sh
```

This writes:

- `artifacts/MY_FIRST_REPORT/METADATA.txt` — exact command + settings (commit this).
- `artifacts/MY_FIRST_REPORT/metrics_play.json` — mean reward/step, dones, latest logged scalars (commit this).
- `artifacts/MY_FIRST_REPORT/videos/` — `rl-video-step-0.mp4` (ignored by `.gitignore` by default).

Summary table across stress folders:

```bash
python3 scripts/merge_stress_report.py   # -> docs/STRESS_REPORT.md
```

## Step 4 — Git

```bash
cd /path/to/isaac-lab-experiments
git init
git add README.md docs scripts artifacts/MY_FIRST_REPORT/METADATA.txt artifacts/MY_FIRST_REPORT/metrics_training_last.json
git status   # confirm mp4 is not staged
git commit -m "Add first eval artifact: training metrics export and play run metadata"
```

If you want the mp4 in git, use **Git LFS** or attach the file elsewhere and only commit a link in `README.md`.

## Step 5 — Report text (for you or hiring packet)

In one page, paste:

- Training: final `Train/mean_reward`, `Train/mean_episode_length`, velocity error metrics (from JSON).
- Eval: what task, checkpoint, command ranges (PLAY config), link or path to video.
- One bullet on **what you’d test next** (command sweep, manipulation, hardware).

## Next iterations

Duplicate `ARTIFACT_NAME` per condition (e.g. `forward_only`, `backward_only`) after adjusting PLAY `lin_vel_x` ranges in `rough_env_cfg.py` and re-running Step 1 + Step 3.
