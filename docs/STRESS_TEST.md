# Stress tests (commands, environment, observations)

## Sync `rough_env_cfg.py` into the container first

PLAY must **keep** `push_robot`, `add_base_mass`, and (for robot friction stress) **`physics_material`** events — do **not** set them to `None` in `UnitreeGo2RoughEnvCfg_PLAY` (this repo’s `source/.../go2/rough_env_cfg.py` is set up that way).

```bash
docker cp ~/isaac-lab-experiments/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/go2/rough_env_cfg.py \
  vscode:/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/go2/rough_env_cfg.py
```

## Full sweep (`stress_test_play.sh`)

Runs **23** jobs (each: video + `metrics_play.json`). ~20+ minutes of GPU time is typical.

```bash
cd ~/isaac-lab-experiments
export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/YOUR_RUN/model_1499.pt"
./scripts/stress_test_play.sh
```

To run a **subset**, comment out unwanted `run_regime ...` blocks in `scripts/stress_test_play.sh`.

## Regime reference

Most **env / obs / dynamics** rows use a fixed **forward mid** command (`vx=0.6`, `vy=0`) so you compare **physics and sensing**, not command speed.

| Folder prefix | What it stresses |
|---------------|------------------|
| `stress_01`–`05` | Command: forward slow/mid/fast, backward, forward+lateral |
| `stress_06`–`08` | Terrain: `max_init_terrain_level` 0 / 4 / 8 |
| `stress_09`–`10` | Ground friction (`scene.terrain.physics_material`) low / high |
| `stress_11` | Robot startup friction range (`events.physics_material`) low |
| `stress_12`–`15` | Observations: corruption on, lin_vel noise, height_scan noise, joint_vel noise |
| `stress_16`–`17` | Commands: high `rel_standing_envs`; forward + high `ang_vel_z` |
| `stress_18`–`19` | Sim gravity; action `joint_pos.delay` |
| `stress_20`–`21` | DR: stronger `push_robot` velocity; wider `add_base_mass` |
| `stress_22` | `NUM_ENVS=8` (batch size) |
| `stress_23` | `PLAY_SEED=12345` |

## Optional: seed on any run

```bash
export PLAY_SEED=42
./scripts/play_and_collect.sh
```

## Merge into one report table

```bash
cd ~/isaac-lab-experiments
python3 scripts/merge_stress_report.py
# writes docs/STRESS_REPORT.md
```

## Single manual regime

```bash
cd ~/isaac-lab-experiments
export ISAAC_CHECKPOINT="logs/rsl_rl/..."
export ARTIFACT_NAME="stress_manual"
export EXTRA_HYDRA='env.commands.base_velocity.ranges.lin_vel_x=\[-0.6,-0.6\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]'
./scripts/play_and_collect.sh
```

Use `\[ \]` so bash inside Docker does not glob `[...]`.

## Training metrics export (unchanged)

```bash
python3 scripts/export_training_metrics.py ~/tb_training_run \
  -o artifacts/MY_FIRST_REPORT/metrics_training_last.json
```

## Git artifacts

Commit **`METADATA.txt`**, **`metrics_play.json`**, **`docs/STRESS_REPORT.md`**. Keep **`*.mp4`** out of git (see root `.gitignore`) or use Git LFS / external links.

## If a Hydra override errors

Paths must match your task’s `params/env.yaml`. Some nested keys (e.g. `push_robot.params.velocity_range.x`) depend on Isaac Lab / OmegaConf version — adjust to match the dump from your run.
