#!/usr/bin/env bash
# Re-run only the regimes that used broken Hydra list syntax (fixed in bb15ab5):
#   imp_08_terrain_hard, imp_12_obs_corruption
#
# Usage:
#   export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/.../model_1499.pt"
#   ./scripts/stress_test_seeded_retry_fix.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export ISAAC_CHECKPOINT="${ISAAC_CHECKPOINT:?Set ISAAC_CHECKPOINT (path inside container)}"
export NUM_ENVS="${NUM_ENVS:-16}"
export VIDEO_LENGTH="${VIDEO_LENGTH:-400}"
SEEDS="${SEEDS:-42 1337 2025 7 9999}"

BASE_MID='env.commands.base_velocity.ranges.lin_vel_x=\[0.6,0.6\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]'

for s in $SEEDS; do
  echo ""
  echo "############################################"
  echo "# imp_08_terrain_hard  |  PLAY_SEED=$s"
  echo "############################################"
  export PLAY_SEED="$s"
  export ARTIFACT_NAME="imp_08_terrain_hard_seed${s}"
  export EXTRA_HYDRA="${BASE_MID} env.scene.terrain.max_init_terrain_level=8"
  ./scripts/play_and_collect.sh
done

for s in $SEEDS; do
  echo ""
  echo "############################################"
  echo "# imp_12_obs_corruption  |  PLAY_SEED=$s"
  echo "############################################"
  export PLAY_SEED="$s"
  export ARTIFACT_NAME="imp_12_obs_corruption_seed${s}"
  export EXTRA_HYDRA="${BASE_MID} env.observations.policy.enable_corruption=true"
  ./scripts/play_and_collect.sh
done

unset PLAY_SEED || true
echo ""
echo "Done. Run: python3 scripts/aggregate_seeded_metrics.py"
