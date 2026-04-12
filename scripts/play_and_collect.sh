#!/usr/bin/env bash
# Run Isaac Lab play (or play_eval_metrics) inside Docker, record video, copy video + metrics JSON.
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
#   export EXTRA_HYDRA='env.commands.base_velocity.ranges.lin_vel_x=\[0.5,0.5\] ...'
#   export PLAY_USE_METRICS=1        # default: use play_eval_metrics.py + metrics_play.json
#   export PLAY_USE_METRICS=0        # use stock play.py (no metrics file)
#   export SKIP_PLAY_EXPORT=1        # default: --skip_export (faster stress sweeps)

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
PLAY_USE_METRICS="${PLAY_USE_METRICS:-1}"
SKIP_PLAY_EXPORT="${SKIP_PLAY_EXPORT:-1}"
METRICS_TMP="/tmp/isaaclab_metrics_${NAME//\//_}.json"

mkdir -p "$OUT"

LOG_DIR_FOR_CP="$(dirname "$CHECKPOINT")"

SKIP_FLAG=""
if [ "$SKIP_PLAY_EXPORT" = 1 ]; then
  SKIP_FLAG="--skip_export"
fi

if [ "$PLAY_USE_METRICS" = 1 ]; then
  docker cp "$ROOT/scripts/isaaclab_rl/play_eval_metrics.py" \
    "$CONTAINER:/workspace/isaaclab/scripts/reinforcement_learning/rsl_rl/play_eval_metrics.py"
  INNER_SCRIPT="scripts/reinforcement_learning/rsl_rl/play_eval_metrics.py"
  METRICS_INLINE="--metrics_json ${METRICS_TMP} ${SKIP_FLAG}"
  DESC="play_eval_metrics.py -> metrics_play.json"
else
  INNER_SCRIPT="scripts/reinforcement_learning/rsl_rl/play.py"
  METRICS_INLINE=""
  DESC="play.py (stock; no metrics_play.json)"
fi

{
  echo "artifact_name=$NAME"
  echo "date=$(date -Iseconds)"
  echo "container=$CONTAINER"
  echo "task=$TASK"
  echo "checkpoint=$CHECKPOINT"
  echo "num_envs=$NUM_ENVS"
  echo "video_length=$VIDEO_LENGTH"
  echo "hydra.run.dir=$HYDRA_DIR"
  echo "metrics_json_container=$METRICS_TMP"
  echo "extra_hydra=${EXTRA_HYDRA:-<none>}"
  echo "play_mode=$DESC"
  echo
  echo "Command (approx): docker exec $CONTAINER ... $INNER_SCRIPT ... $METRICS_INLINE ... hydra... $EXTRA_HYDRA"
} | tee "$OUT/METADATA.txt"

docker exec "$CONTAINER" bash -lc "cd /workspace/isaaclab && /isaac-sim/python.sh $INNER_SCRIPT \
  --task \"$TASK\" \
  --num_envs \"$NUM_ENVS\" \
  --checkpoint \"$CHECKPOINT\" \
  --headless --enable_cameras --video --video_length \"$VIDEO_LENGTH\" \
  ${METRICS_INLINE} \
  hydra.run.dir=\"$HYDRA_DIR\" \
  ${EXTRA_HYDRA}"

if [ "$PLAY_USE_METRICS" = 1 ]; then
  docker cp "$CONTAINER:$METRICS_TMP" "$OUT/metrics_play.json"
fi

mkdir -p "$OUT/videos"
docker cp "$CONTAINER:/workspace/isaaclab/${LOG_DIR_FOR_CP}/videos/play/." "$OUT/videos/" || {
  echo "WARN: docker cp videos failed — check path LOG_DIR_FOR_CP=$LOG_DIR_FOR_CP inside container."
  exit 1
}

echo ""
echo "Done. Video folder: $OUT/videos"
ls -la "$OUT/videos"
if [ "$PLAY_USE_METRICS" = 1 ]; then
  echo "Metrics: $OUT/metrics_play.json"
  echo "Summary table: python3 scripts/merge_stress_report.py"
fi
echo ""
echo "Next: copy training metrics JSON (optional):"
echo "  python3 scripts/export_training_metrics.py PATH_TO_TRAINING_RUN_DIR -o $OUT/metrics_training_last.json"
