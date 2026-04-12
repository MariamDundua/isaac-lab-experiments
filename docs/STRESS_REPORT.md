# Stress / play eval summary

Auto-generated from `artifacts/*/metrics_play.json`. Re-run: `python3 scripts/merge_stress_report.py`.

| Run folder | Steps | Mean reward/step | Total dones | err_vel_xy† | err_vel_yaw† | Hydra overrides (from METADATA) |
|------------|------:|-----------------:|------------:|------------:|-------------:|----------------------------------|
| stress_01_fwd_slow | 400 | 0.0398 | 0 | 0.0000 | 0.0000 | `env.commands.base_velocity.ranges.lin_vel_x=\[0.3,0.3\] env.commands.base_vel...` |
| stress_02_fwd_mid | 400 | 0.0374 | 0 | 0.0000 | 0.0000 | `env.commands.base_velocity.ranges.lin_vel_x=\[0.6,0.6\] env.commands.base_vel...` |
| stress_03_fwd_fast | 400 | 0.0342 | 0 | 0.0000 | 0.0000 | `env.commands.base_velocity.ranges.lin_vel_x=\[1.0,1.0\] env.commands.base_vel...` |
| stress_04_back_mid | 400 | 0.0403 | 0 | 0.0000 | 0.0000 | `env.commands.base_velocity.ranges.lin_vel_x=\[-0.6,-0.6\] env.commands.base_v...` |
| stress_05_fwd_lat | 400 | 0.0387 | 0 | 0.0000 | 0.0000 | `env.commands.base_velocity.ranges.lin_vel_x=\[0.4,0.4\] env.commands.base_vel...` |

† From last `extras['log']` snapshot during the rollout (often updated around env resets); may be empty for very short clips.
