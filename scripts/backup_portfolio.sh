#!/usr/bin/env bash
# Bundle artifacts (videos, metrics JSON, METADATA) and optionally RSL-RL logs/checkpoints
# from the Isaac Docker container into a single .tar.gz for upload (S3, Drive, HF, etc.).
#
# Usage (from anywhere):
#   ./scripts/backup_portfolio.sh
#   ./scripts/backup_portfolio.sh --docker-logs
#   ./scripts/backup_portfolio.sh --docker-run logs/rsl_rl/unitree_go2_rough/2026-04-12_18-11-57
#
# Env:
#   ISAAC_CONTAINER   Docker name (default: vscode)
#   ISAAC_LAB_ROOT    Path inside container to Isaac Lab root (default: /workspace/isaaclab)
#   BACKUP_OUT_DIR    Host directory for the archive (default: <repo>/backups)
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${ISAAC_CONTAINER:-vscode}"
LAB_ROOT="${ISAAC_LAB_ROOT:-/workspace/isaaclab}"
OUT_DIR="${BACKUP_OUT_DIR:-$ROOT/backups}"
_tmp_pat="${TMPDIR:-/tmp}/isaaclab_backup.XXXXXX"
STAGING="$(mktemp -d "$_tmp_pat")"
cleanup() { rm -rf "$STAGING"; }
trap cleanup EXIT

WITH_DOCKER_LOGS=0
DOCKER_RUN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --docker-logs) WITH_DOCKER_LOGS=1; shift ;;
    --docker-run)
      DOCKER_RUN="${2:?--docker-run requires a path under $LAB_ROOT}"
      shift 2
      ;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$OUT_DIR"
TS="$(date +%Y-%m-%d_%H-%M-%S)"
ARCHIVE="$OUT_DIR/isaac-lab-experiments_backup_${TS}.tar.gz"

if [[ ! -d "$ROOT/artifacts" ]]; then
  echo "No artifacts/ under $ROOT — nothing to back up." >&2
  exit 1
fi

echo "Staging from repo: $ROOT"
cp -a "$ROOT/artifacts" "$STAGING/artifacts"
if [[ -d "$ROOT/docs" ]]; then
  cp -a "$ROOT/docs" "$STAGING/docs"
fi

if [[ "$WITH_DOCKER_LOGS" -eq 1 ]]; then
  echo "Copying $CONTAINER:$LAB_ROOT/logs/rsl_rl (may be large)…"
  mkdir -p "$STAGING/from_container"
  docker cp "$CONTAINER:$LAB_ROOT/logs/rsl_rl" "$STAGING/from_container/logs_rsl_rl" \
    || { echo "docker cp failed — is the container running and paths correct?" >&2; exit 1; }
fi

if [[ -n "$DOCKER_RUN" ]]; then
  REMOTE="$LAB_ROOT/${DOCKER_RUN#/}"
  echo "Copying single run: $CONTAINER:$REMOTE …"
  mkdir -p "$STAGING/from_container"
  base="$(basename "$DOCKER_RUN")"
  docker cp "$CONTAINER:$REMOTE" "$STAGING/from_container/$base" \
    || { echo "docker cp failed — check container name and remote path." >&2; exit 1; }
fi

echo "Writing archive: $ARCHIVE"
tar -czf "$ARCHIVE" -C "$STAGING" .
ls -lh "$ARCHIVE"
echo "Done. Upload this file to cloud storage or attach it to a GitHub Release."
