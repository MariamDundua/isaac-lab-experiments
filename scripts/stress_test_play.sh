#!/usr/bin/env bash
# Run several play+video jobs with different Hydra command-range overrides (stress regimes).
#
# Usage:
#   cd ~/isaac-lab-experiments
#   export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/YOUR_RUN/model_1499.pt"
#   ./scripts/stress_test_play.sh
#
# Optional: NUM_ENVS, VIDEO_LENGTH, ISAAC_CONTAINER, TASK

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export ISAAC_CHECKPOINT="${ISAAC_CHECKPOINT:?Set ISAAC_CHECKPOINT (path inside container)}"
export NUM_ENVS="${NUM_ENVS:-16}"
export VIDEO_LENGTH="${VIDEO_LENGTH:-400}"

run_regime() {
  local artifact=$1
  local hydra_extra=$2
  local label=$3
  echo ""
  echo "############################################"
  echo "# $label"
  echo "############################################"
  export ARTIFACT_NAME="$artifact"
  export EXTRA_HYDRA="$hydra_extra"
  ./scripts/play_and_collect.sh
}

# Regime id | Hydra overrides (lin_vel x,y as fixed ranges) | human label
# Note: \[ \] so inner bash does not treat [...] as a glob inside docker bash -lc "...".
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
  "Forward + lateral band (vx=0.4, vy in [-0.15,0.15])"

echo ""
echo "All stress runs finished. Artifacts under: $ROOT/artifacts/stress_*/"
