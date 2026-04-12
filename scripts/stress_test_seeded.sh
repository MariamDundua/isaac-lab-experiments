#!/usr/bin/env bash
# Multi-seed stress runs for a *small* set of high-signal regimes (mean ± spread across seeds).
#
# Default: 6 regimes × 5 seeds = 30 Isaac Sim runs.
#
# Usage:
#   cd ~/isaac-lab-experiments
#   export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/YOUR_RUN/model_1499.pt"
#   ./scripts/stress_test_seeded.sh
#
# Optional:
#   SEEDS="42 43 44"     # fewer or more seeds (space-separated)
#   NUM_ENVS VIDEO_LENGTH ISAAC_CONTAINER TASK

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export ISAAC_CHECKPOINT="${ISAAC_CHECKPOINT:?Set ISAAC_CHECKPOINT (path inside container)}"
export NUM_ENVS="${NUM_ENVS:-16}"
export VIDEO_LENGTH="${VIDEO_LENGTH:-400}"

# Space-separated list of integer seeds
SEEDS="${SEEDS:-42 1337 2025 7 9999}"

BASE_MID='env.commands.base_velocity.ranges.lin_vel_x=\[0.6,0.6\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]'

run_seeded_regime() {
  local base=$1
  local hydra_extra=$2
  local label=$3
  local s
  for s in $SEEDS; do
    echo ""
    echo "############################################"
    echo "# $label  |  PLAY_SEED=$s"
    echo "############################################"
    export PLAY_SEED="$s"
    export ARTIFACT_NAME="${base}_seed${s}"
    export EXTRA_HYDRA="$hydra_extra"
    ./scripts/play_and_collect.sh
  done
  unset PLAY_SEED || true
}

echo "Multi-seed stress: seeds=[$SEEDS] ($(echo "$SEEDS" | wc -w) runs per regime)"
echo ""

run_seeded_regime "imp_02_fwd_mid" \
  'env.commands.base_velocity.ranges.lin_vel_x=\[0.6,0.6\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]' \
  "Important: forward mid (vx=0.6)"

run_seeded_regime "imp_03_fwd_fast" \
  'env.commands.base_velocity.ranges.lin_vel_x=\[1.0,1.0\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]' \
  "Important: forward fast (vx=1.0)"

run_seeded_regime "imp_08_terrain_hard" \
  "${BASE_MID} env.scene.terrain.max_init_terrain_level=\[8\]" \
  "Important: hard terrain spawn (max_init=8)"

run_seeded_regime "imp_12_obs_corruption" \
  "${BASE_MID} env.observations.policy.enable_corruption=\[true\]" \
  "Important: observation corruption ON"

run_seeded_regime "imp_20_push_hi" \
  "${BASE_MID} env.events.push_robot.params.velocity_range.x=\[-1.5,1.5\] env.events.push_robot.params.velocity_range.y=\[-0.45,0.45\]" \
  "Important: strong push velocities"

run_seeded_regime "imp_21_mass_hi" \
  "${BASE_MID} env.events.add_base_mass.params.mass_distribution_params=\[0.0,10.0\]" \
  "Important: heavy add-base-mass range"

echo ""
echo "Done. Artifacts: $ROOT/artifacts/imp_*_seed*/"
echo "Aggregate: python3 scripts/aggregate_seeded_metrics.py"
echo "Full table:  python3 scripts/merge_stress_report.py"
