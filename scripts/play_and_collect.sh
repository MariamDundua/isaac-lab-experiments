#!/usr/bin/env bash
# Run Isaac Lab play.py inside the Docker "vscode" container, record video, copy artifacts to this repo.
#
# Usage (from repo root):
#   export ISAAC_CHECKPOINT="logs/rsl_rl/unitree_go2_rough/2026-04-12_18-11-57/model_1499.pt"
#   export ARTIFACT_NAME="2026-04-12_forward_eval"
#   ./scripts/play_and_collect.sh
#
# Optional:
#   export ISAAC_CONTAINER=vscode
#   export NUM_ENVS=16
#   export VIDEO_LENGTH=400
#   export TASK="Isaac-Velocity-Rough-Unitree-Go2-Play-v0"
#   export EXTRA_HYDRA='env.commands.base_velocity.ranges.lin_vel_x=\[0.5,0.5\] env.commands.base_velocity.ranges.lin_vel_y=\[0.0,0.0\]'
#       (optional Hydra overrides for command ranges — see docs/STRESS_TEST.md)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${ISAAC_CONTAINER:-vscode}"
TASK="${TASK:-Isaac-Velocity-Rough-Unitree-Go2-Play-v0}"
CHECKPOINT="${ISAAC_CHECKPOINT:?Set ISAAC_CHECKPOINT to checkpoint path inside container, e.g. logs/rsl_rl/.../model_1499.pt}"
NAME="${ARTIFACT_NAME:-eval_$(date +%Y-%m-%d_%H-%M-%S)}"
NUM_ENVS="${NUM_ENVS:-16}"
VIDEO_LENGTH="${VIDEO_LENGTH:-400}"
OUT="$ROOT/artifacts/$NAME"
HYDRA_DIR="/tmp/isaaclab_hydra_eval_${NAME//\//_}"
EXTRA_HYDRA="${EXTRA_HYDRA:-}"

mkdir -p "$OUT"

# log_dir = dirname(checkpoint) inside container — video is written to log_dir/videos/play/
LOG_DIR_FOR_CP="$(dirname "$CHECKPOINT")"

{
  echo "artifact_name=$NAME"
  echo "date=$(date -Iseconds)"
  echo "container=$CONTAINER"
  echo "task=$TASK"
  echo "checkpoint=$CHECKPOINT"
  echo "num_envs=$NUM_ENVS"
  echo "video_length=$VIDEO_LENGTH"
  echo "hydra.run.dir=$HYDRA_DIR"
  echo "extra_hydra=${EXTRA_HYDRA:-<none>}"
  echo
  echo "Command:"
  echo "docker exec $CONTAINER bash -lc 'cd /workspace/isaaclab && /isaac-sim/python.sh scripts/reinforcement_learning/rsl_rl/play.py --task $TASK --num_envs $NUM_ENVS --checkpoint $CHECKPOINT --headless --enable_cameras --video --video_length $VIDEO_LENGTH hydra.run.dir=$HYDRA_DIR ${EXTRA_HYDRA}'"
} | tee "$OUT/METADATA.txt"

docker exec "$CONTAINER" bash -lc "cd /workspace/isaaclab && /isaac-sim/python.sh scripts/reinforcement_learning/rsl_rl/play.py \
  --task \"$TASK\" \
  --num_envs \"$NUM_ENVS\" \
  --checkpoint \"$CHECKPOINT\" \
  --headless --enable_cameras --video --video_length \"$VIDEO_LENGTH\" \
  hydra.run.dir=\"$HYDRA_DIR\" \
  ${EXTRA_HYDRA}"

mkdir -p "$OUT/videos"
docker cp "$CONTAINER:/workspace/isaaclab/${LOG_DIR_FOR_CP}/videos/play/." "$OUT/videos/" || {
  echo "WARN: docker cp videos failed — check path LOG_DIR_FOR_CP=$LOG_DIR_FOR_CP inside container."
  exit 1
}

echo ""
echo "Done. Video folder: $OUT/videos"
ls -la "$OUT/videos"
echo ""
echo "Next: copy training metrics JSON (optional):"
echo "  python3 scripts/export_training_metrics.py PATH_TO_TRAINING_RUN_DIR -o $OUT/metrics_training_last.json"
