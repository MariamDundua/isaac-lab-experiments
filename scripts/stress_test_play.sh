#!/usr/bin/env bash
# Command, environment, and observation stress sweeps (Hydra overrides + play_eval_metrics).
#
# Prerequisites:
#   - Sync updated go2/rough_env_cfg.py (PLAY keeps push, mass, physics_material) into the container.
#   - vscode container running, checkpoint inside container.
#
# Usage:
#   cd ~/isaac-lab-experiments
#   export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/YOUR_RUN/model_1499.pt"
#   ./scripts/stress_test_play.sh
#
# Optional: NUM_ENVS, VIDEO_LENGTH, ISAAC_CONTAINER, TASK
# To run a subset, comment out unwanted run_regime blocks below.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export ISAAC_CHECKPOINT="${ISAAC_CHECKPOINT:?Set ISAAC_CHECKPOINT (path inside container)}"
export NUM_ENVS="${NUM_ENVS:-16}"
export VIDEO_LENGTH="${VIDEO_LENGTH:-400}"

# Common forward command for env/obs/dynamics tests (matches mid-speed baseline).
BASE_MID='env.commands.base_velocity.ranges.lin_vel_x=\[0.6,0.6\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]'

run_idx=0

run_regime() {
  local artifact=$1
  local hydra_extra=$2
  local label=$3
  run_idx=$((run_idx + 1))
  echo ""
  echo "############################################"
  echo "# [$run_idx] $label"
  echo "############################################"
  export ARTIFACT_NAME="$artifact"
  export EXTRA_HYDRA="$hydra_extra"
  ./scripts/play_and_collect.sh
}

# --- 1–5: velocity command stress (original) ---
run_regime "stress_01_fwd_slow" \
  'env.commands.base_velocity.ranges.lin_vel_x=\[0.3,0.3\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]' \
  "Forward slow (vx=0.3)"

run_regime "stress_02_fwd_mid" \
  'env.commands.base_velocity.ranges.lin_vel_x=\[0.6,0.6\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]' \
  "Forward mid (vx=0.6)"

run_regime "stress_03_fwd_fast" \
  'env.commands.base_velocity.ranges.lin_vel_x=\[1.0,1.0\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]' \
  "Forward fast (vx=1.0)"

run_regime "stress_04_back_mid" \
  'env.commands.base_velocity.ranges.lin_vel_x=\[-0.6,-0.6\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]' \
  "Backward mid (vx=-0.6)"

run_regime "stress_05_fwd_lat" \
  'env.commands.base_velocity.ranges.lin_vel_x=\[0.4,0.4\] env.commands.base_velocity.ranges.lin_vel_y=\[-0.15,0.15\]' \
  "Forward + lateral band"

# --- 6–8: terrain init difficulty (caps max initial curriculum level) ---
run_regime "stress_06_terrain_maxinit_0" \
  "${BASE_MID} env.scene.terrain.max_init_terrain_level=\[0\]" \
  "Terrain: max_init_terrain_level=0 (easiest spawn band)"

run_regime "stress_07_terrain_maxinit_4" \
  "${BASE_MID} env.scene.terrain.max_init_terrain_level=\[4\]" \
  "Terrain: max_init_terrain_level=4"

run_regime "stress_08_terrain_maxinit_8" \
  "${BASE_MID} env.scene.terrain.max_init_terrain_level=\[8\]" \
  "Terrain: max_init_terrain_level=8 (harder)"

# --- 9–10: ground (terrain) friction ---
run_regime "stress_09_ground_friction_low" \
  "${BASE_MID} env.scene.terrain.physics_material.static_friction=\[0.28\] env.scene.terrain.physics_material.dynamic_friction=\[0.22\]" \
  "Ground friction low (slippery)"

run_regime "stress_10_ground_friction_high" \
  "${BASE_MID} env.scene.terrain.physics_material.static_friction=\[1.45\] env.scene.terrain.physics_material.dynamic_friction=\[1.25\]" \
  "Ground friction high (sticky)"

# --- 11: robot-body friction randomization range (startup event) ---
run_regime "stress_11_robot_friction_low" \
  "${BASE_MID} env.events.physics_material.params.static_friction_range=\[0.12,0.18\] env.events.physics_material.params.dynamic_friction_range=\[0.1,0.15\]" \
  "Robot physics_material: low friction range"

# --- 12–15: observations ---
run_regime "stress_12_obs_corruption_on" \
  "${BASE_MID} env.observations.policy.enable_corruption=\[true\]" \
  "Obs: enable_corruption=true (train-like noise)"

run_regime "stress_13_obs_linvel_noise_hi" \
  "${BASE_MID} env.observations.policy.base_lin_vel.noise.n_min=\[-0.35\] env.observations.policy.base_lin_vel.noise.n_max=\[0.35\]" \
  "Obs: high base_lin_vel uniform noise"

run_regime "stress_14_obs_height_scan_noise_hi" \
  "${BASE_MID} env.observations.policy.height_scan.noise.n_min=\[-0.12\] env.observations.policy.height_scan.noise.n_max=\[0.12\]" \
  "Obs: high height_scan noise"

run_regime "stress_15_obs_joint_vel_noise_hi" \
  "${BASE_MID} env.observations.policy.joint_vel.noise.n_min=\[-3.0\] env.observations.policy.joint_vel.noise.n_max=\[3.0\]" \
  "Obs: high joint_vel noise"

# --- 16–17: command distribution ---
run_regime "stress_16_cmd_standing_mix" \
  "${BASE_MID} env.commands.base_velocity.rel_standing_envs=\[0.45\]" \
  "Command: ~45% standing envs"

run_regime "stress_17_cmd_yaw_spin" \
  'env.commands.base_velocity.ranges.lin_vel_x=\[0.35,0.35\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\] env.commands.base_velocity.ranges.ang_vel_z=\[1.0,1.0\]' \
  "Command: forward slow + high yaw rate"

# --- 18–19: sim / actuation ---
run_regime "stress_18_gravity_heavy" \
  "${BASE_MID} env.sim.gravity=\[0.0,0.0,-13.5\]" \
  "Sim: stronger gravity (-13.5)"

run_regime "stress_19_action_delay_hi" \
  "${BASE_MID} env.actions.joint_pos.delay=\[5,8\]" \
  "Actions: joint_pos delay (5,8) steps"

# --- 20–21: domain randomization magnitude (requires PLAY to keep events) ---
run_regime "stress_20_push_velocity_hi" \
  "${BASE_MID} env.events.push_robot.params.velocity_range.x=\[-1.5,1.5\] env.events.push_robot.params.velocity_range.y=\[-0.45,0.45\]" \
  "Events: stronger interval push velocity"

run_regime "stress_21_add_mass_hi" \
  "${BASE_MID} env.events.add_base_mass.params.mass_distribution_params=\[0.0,10.0\]" \
  "Events: heavier add_base_mass range"

# --- 22: fewer parallel envs (lighter GPU / different batch stats) ---
save_ne=${NUM_ENVS}
export NUM_ENVS=8
run_regime "stress_22_num_envs_8" \
  "${BASE_MID}" \
  "Infrastructure: NUM_ENVS=8"
export NUM_ENVS="$save_ne"

# --- 23: different seed ---
save_seed=${PLAY_SEED:-}
export PLAY_SEED=12345
run_regime "stress_23_seed_12345" \
  "${BASE_MID}" \
  "Repeatability: PLAY_SEED=12345"
export PLAY_SEED="$save_seed"

echo ""
echo "All stress runs finished ($run_idx jobs). Artifacts: $ROOT/artifacts/stress_*/"
echo "Summary: python3 scripts/merge_stress_report.py"
