# Stress tests vs what you already ran

## What `MY_FIRST_REPORT` actually was (**not** a multi-regime stress test)

It was **one** `play.py` run with:

- **Task:** `Isaac-Velocity-Rough-Unitree-Go2-Play-v0`
- **Checkpoint:** `model_1499.pt`
- **16 parallel envs**, **400** video steps
- **Command ranges:** whatever your **PLAY** env config applies **plus** any defaults from Hydra (your `rough_env_cfg.py` PLAY class pins `lin_vel_x` to forward-only `(0,1)` and `lin_vel_y` to `0` when that code is synced into the container).

So you got a **single-condition demo video** (rough terrain, forward-only x, zero lateral y), **not** a sweep over forward/backward/speed.

## What a **stress test** means here

A **stress test** = **same checkpoint**, **same task**, but **different commanded velocity ranges** (and optionally different seeds), then compare **videos + qualitative behavior** (falls, backward when command is forward, etc.).

Suggested regimes (all use **fixed** ranges so every env in the rollout sees the same command family):

| ID | Intent | `lin_vel_x` | `lin_vel_y` |
|----|--------|-------------|-------------|
| `stress_01_fwd_slow` | Forward slow | `[0.3, 0.3]` | `[0.0, 0.0]` |
| `stress_02_fwd_mid` | Forward mid | `[0.6, 0.6]` | `[0.0, 0.0]` |
| `stress_03_fwd_fast` | Forward fast | `[1.0, 1.0]` | `[0.0, 0.0]` |
| `stress_04_back_mid` | Backward mid | `[-0.6, -0.6]` | `[0.0, 0.0]` |
| `stress_05_lat_small` | Small lateral | `[0.4, 0.4]` | `[-0.15, 0.15]` |

Later you can add **yaw** via `env.commands.base_velocity.ranges.ang_vel_z=...` if you use heading-off mode consistently.

Hydra overrides merge into the env config (see Isaac Lab `hydra_task_config`).

## Code: run the full sweep (host)

From repo root, after `vscode` container is up and checkpoint exists **inside** the container:

```bash
cd ~/isaac-lab-experiments
chmod +x scripts/stress_test_play.sh
export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/2026-04-12_18-11-57/model_1499.pt"
./scripts/stress_test_play.sh
```

Each regime runs `play_and_collect.sh` and writes `artifacts/stress_XX_*/`.

## Code: run **one** regime manually

```bash
cd ~/isaac-lab-experiments
export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/2026-04-12_18-11-57/model_1499.pt"
export ARTIFACT_NAME="stress_manual_backward"
# \[ \] avoids bash glob on [...] inside docker bash -lc.
export EXTRA_HYDRA='env.commands.base_velocity.ranges.lin_vel_x=\[-0.6,-0.6\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]'
./scripts/play_and_collect.sh
```

## Code: export training metrics (unchanged)

```bash
cd ~/isaac-lab-experiments
python3 scripts/export_training_metrics.py ~/tb_training_run \
  -o artifacts/MY_FIRST_REPORT/metrics_training_last.json
```

## After the sweep

- Fill a **table** in your report: regime → “stable / falls / wrong-way when cmd forward”.
- Commit only **`METADATA.txt`** per folder; keep **mp4** out of git or use **Git LFS**.
