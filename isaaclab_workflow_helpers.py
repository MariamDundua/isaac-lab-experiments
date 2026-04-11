#!/usr/bin/env python3
"""
Isaac Lab + Docker workflow (this agent / remote server)

================================================================================
MAIN PIECES OF “CODE” YOU TOUCH
================================================================================
1) Task env configs (edit on host, then sync into container):
   - velocity_env_cfg.py
     .../isaaclab_tasks/manager_based/locomotion/velocity/velocity_env_cfg.py
   - Go2 rough
     .../velocity/config/go2/rough_env_cfg.py
   Gym ids: Isaac-Velocity-Rough-Unitree-Go2-v0 (train-like),
            Isaac-Velocity-Rough-Unitree-Go2-Play-v0 (play / video)

2) Play script (inside container, do not edit for normal use):
   scripts/reinforcement_learning/rsl_rl/play.py

3) Checkpoints & videos:
   Host mirror (Cursor):  ~/isaaclab-from-container/logs/rsl_rl/...
   Container (sim runs): /workspace/isaaclab/logs/rsl_rl/...

================================================================================
PATHS: HOST vs CONTAINER
================================================================================
- On the HOST (shadeform@...):  /home/shadeform/isaaclab-from-container/...
- In the `vscode` CONTAINER:      /workspace/isaaclab/...
Unless you use docker-compose.host-isaaclab.yml bind-mount, these are *not*
the same filesystem — use `docker cp` both ways after edits on the host.

================================================================================
UPLOAD FILES
================================================================================
A) Laptop → server (run on your Mac):
   scp "/path/local/model.pt" shadeform@SERVER:/home/shadeform/isaaclab-from-container/logs/rsl_rl/unitree_go2_rough/RUN/

B) Host → container (run on server):
   docker cp /home/shadeform/isaaclab-from-container/logs/.../model.pt \\
     vscode:/workspace/isaaclab/logs/.../

C) Container → host (videos, logs):
   docker cp vscode:/workspace/isaaclab/logs/.../videos/play/rl-video-step-0.mp4 \\
     /home/shadeform/

================================================================================
RUN PLAY / VIDEO (always inside container)
================================================================================
   docker exec -it vscode bash
   cd /workspace/isaaclab
   /isaac-sim/python.sh scripts/reinforcement_learning/rsl_rl/play.py \\
     --task Isaac-Velocity-Rough-Unitree-Go2-Play-v0 \\
     --num_envs 32 \\
     --checkpoint logs/rsl_rl/unitree_go2_rough/YOUR_RUN/model.pt \\
     --headless --enable_cameras --video --video_length 800 \\
     hydra.run.dir=/tmp/isaaclab_hydra

Use /isaac-sim/python.sh (plain `python` may be missing in non-login docker exec).

================================================================================
PERMISSIONS / HYDRA / VIDEO FOLDER
================================================================================
- Hydra wants ./outputs under cwd → use hydra.run.dir=/tmp/isaaclab_hydra, or:
  docker exec -u root vscode mkdir -p /workspace/isaaclab/outputs
  docker exec -u root vscode chown -R isaac-sim:isaac-sim /workspace/isaaclab/outputs
- RecordVideo writes under the run log dir → chown that run folder to isaac-sim if needed:
  docker exec -u root vscode chown -R isaac-sim:isaac-sim /workspace/isaaclab/logs/rsl_rl/.../RUN

================================================================================
VIDEO: ROBOT INVISIBLE / SIDEWAYS
================================================================================
ViewerCfg.eye / lookat are offsets from viewer_origin (see ViewportCameraController).
Use origin_type=\"env\" + env_index=0 for a stable yard shot; avoid huge world
coordinates with origin_type=\"asset_root\".
"""

from __future__ import annotations

import argparse
import subprocess
import urllib.request
from pathlib import Path


DEFAULT_HOST_LOG_ROOT = Path("/home/shadeform/isaaclab-from-container/logs/rsl_rl")
DEFAULT_CONTAINER_LOG_ROOT = Path("/workspace/isaaclab/logs/rsl_rl")
DEFAULT_HOST_PROJECT = Path("/home/shadeform/isaaclab-from-container")
DEFAULT_CONTAINER_PROJECT = Path("/workspace/isaaclab")
DEFAULT_CONTAINER_NAME = "vscode"


def host_to_container_path(host_path: str | Path) -> Path:
    host_path = Path(host_path).resolve()
    host_root = DEFAULT_HOST_PROJECT.resolve()
    rel = host_path.relative_to(host_root)
    return DEFAULT_CONTAINER_PROJECT / rel


def container_to_host_path(container_path: str | Path) -> Path:
    container_path = Path(container_path)
    prefix = DEFAULT_CONTAINER_PROJECT
    s = str(container_path)
    if not s.startswith(str(prefix)):
        raise ValueError(f"Path must start with {prefix}: {container_path}")
    rel = container_path.relative_to(prefix)
    return DEFAULT_HOST_PROJECT / rel


def fetch_public_ipv4(timeout_s: float = 5.0) -> str | None:
    for url in (
        "https://ifconfig.me/ip",
        "https://api.ipify.org",
        "https://icanhazip.com",
    ):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "isaaclab-workflow-helpers"})
            with urllib.request.urlopen(req, timeout=timeout_s) as r:
                text = r.read().decode().strip()
                if text and "." in text:
                    return text.split()[0]
        except OSError:
            continue
    return None


def print_cheatsheet() -> None:
    """Print the long module docstring (workflow summary)."""
    import inspect

    print(inspect.getdoc(__import__(__name__)) or "")


def print_scp_to_server(
    *,
    local_file: str | Path,
    remote_dir: str | Path,
    user: str = "shadeform",
    host: str | None = None,
) -> str:
    if host is None:
        host = fetch_public_ipv4() or "YOUR_SERVER_IP"
    local_file = Path(local_file).expanduser()
    remote_dir = str(remote_dir).rstrip("/")
    cmd = f'scp "{local_file}" {user}@{host}:{remote_dir}/'
    print(cmd)
    return cmd


def print_scp_checkpoint_example(
    *,
    run_folder: str = "unitree_go2_rough/2026-03-28_08-36-21",
    filename: str = "model_2600.pt",
    user: str = "shadeform",
    host: str | None = None,
) -> None:
    dest = DEFAULT_HOST_LOG_ROOT / run_folder
    print("# On your Mac (fix LOCAL path):")
    print_scp_to_server(
        local_file=f"/Users/you/Documents/Isaac_lab/{filename}",
        remote_dir=dest,
        user=user,
        host=host,
    )
    print(f"# Server path: {dest / filename}")
    print(f"# Container path: {host_to_container_path(dest / filename)}")


def print_docker_cp_into_container(
    *,
    host_src: str | Path,
    container_dest: str | Path,
    container_name: str = DEFAULT_CONTAINER_NAME,
) -> str:
    cmd = f'docker cp "{Path(host_src).resolve()}" {container_name}:{container_dest}'
    print(cmd)
    return cmd


def print_sync_task_configs(container_name: str = DEFAULT_CONTAINER_NAME) -> None:
    """Print docker cp lines for velocity + Go2 rough env configs."""
    base = DEFAULT_HOST_PROJECT / "source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity"
    v = base / "velocity_env_cfg.py"
    g = base / "config/go2/rough_env_cfg.py"
    print("# Host -> container (run on server)")
    print_docker_cp_into_container(host_src=v, container_dest="/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/", container_name=container_name)
    print_docker_cp_into_container(host_src=g, container_dest="/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/go2/", container_name=container_name)
    print("# Fix ownership inside container")
    print(
        f"docker exec -u root {container_name} chown isaac-sim:isaac-sim "
        "/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/velocity_env_cfg.py "
        "/workspace/isaaclab/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/go2/rough_env_cfg.py"
    )


def print_play_command(
    *,
    task: str = "Isaac-Velocity-Rough-Unitree-Go2-Play-v0",
    checkpoint_rel: str = "logs/rsl_rl/unitree_go2_rough/2026-03-28_08-36-21/model_2600.pt",
    num_envs: int = 32,
    headless: bool = True,
    enable_cameras: bool = False,
    video: bool = False,
    video_length: int = 200,
    hydra_dir: str = "/tmp/isaaclab_hydra",
) -> str:
    parts = [
        "cd /workspace/isaaclab && /isaac-sim/python.sh scripts/reinforcement_learning/rsl_rl/play.py",
        f"  --task {task}",
        f"  --num_envs {num_envs}",
        f"  --checkpoint {checkpoint_rel}",
    ]
    if headless:
        parts.append("  --headless")
    if enable_cameras or video:
        parts.append("  --enable_cameras")
    if video:
        parts.extend(["  --video", f"  --video_length {video_length}"])
    parts.append(f"  hydra.run.dir={hydra_dir}")
    cmd = " \\\n".join(parts)
    print("# Inside: docker exec -it vscode bash")
    print(cmd)
    return cmd


def print_docker_exec_play_one_liner(
    *,
    task: str = "Isaac-Velocity-Rough-Unitree-Go2-Play-v0",
    checkpoint_rel: str = "logs/rsl_rl/unitree_go2_rough/2026-03-28_08-36-21/model_2600.pt",
    num_envs: int = 32,
    video: bool = True,
    video_length: int = 800,
    container_name: str = DEFAULT_CONTAINER_NAME,
) -> str:
    inner = (
        f"cd /workspace/isaaclab && /isaac-sim/python.sh scripts/reinforcement_learning/rsl_rl/play.py "
        f"--task {task} --num_envs {num_envs} --checkpoint {checkpoint_rel} "
        f"--headless --enable_cameras"
    )
    if video:
        inner += f" --video --video_length {video_length}"
    inner += " hydra.run.dir=/tmp/isaaclab_hydra"
    cmd = f'docker exec -w /workspace/isaaclab {container_name} bash -lc {repr(inner)}'
    print("# From host (one shot, no interactive shell)")
    print(cmd)
    return cmd


def run_local_copy(src: str | Path, dst_dir: str | Path, sudo: bool = False) -> None:
    src, dst_dir = Path(src), Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    cmd = ["cp", str(src), str(dst)]
    if sudo:
        cmd = ["sudo", *cmd]
    subprocess.run(cmd, check=True)
    print(f"Copied -> {dst}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Isaac Lab upload / Docker / play helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("cheatsheet", help="Print full workflow doc").set_defaults(func=lambda _: print_cheatsheet())

    p_ip = sub.add_parser("public-ip", help="Print public IPv4 (scp target hint)")
    p_ip.set_defaults(func=lambda _: print(fetch_public_ipv4() or "unknown"))

    p_scp = sub.add_parser("scp-example", help="Print example scp for a checkpoint")
    p_scp.add_argument("--run-folder", default="unitree_go2_rough/2026-03-28_08-36-21")
    p_scp.add_argument("--filename", default="model_2600.pt")
    p_scp.add_argument("--user", default="shadeform")
    p_scp.add_argument("--host", default=None)
    p_scp.set_defaults(
        func=lambda a: print_scp_checkpoint_example(
            run_folder=a.run_folder,
            filename=a.filename,
            user=a.user,
            host=a.host,
        )
    )

    p_sync = sub.add_parser("sync-configs", help="Print docker cp + chown for velocity + rough_env_cfg")
    p_sync.add_argument("--container", default=DEFAULT_CONTAINER_NAME)
    p_sync.set_defaults(func=lambda a: print_sync_task_configs(container_name=a.container))

    p_map = sub.add_parser("map-path", help="Map host path <-> container path under isaaclab-from-container")
    p_map.add_argument("path")
    p_map.add_argument("--to-host", action="store_true")
    p_map.set_defaults(func=None)

    p_play = sub.add_parser("play-cmd", help="Print play.py (inside container)")
    p_play.add_argument("--task", default="Isaac-Velocity-Rough-Unitree-Go2-Play-v0")
    p_play.add_argument("--checkpoint", default="logs/rsl_rl/unitree_go2_rough/2026-03-28_08-36-21/model_2600.pt")
    p_play.add_argument("--num-envs", type=int, default=32)
    p_play.add_argument("--video", action="store_true")
    p_play.add_argument("--video-length", type=int, default=800)
    p_play.add_argument("--enable-cameras", action="store_true")
    p_play.set_defaults(func=None)

    p_one = sub.add_parser("play-docker", help="Print one-line docker exec ... play.py from host")
    p_one.add_argument("--task", default="Isaac-Velocity-Rough-Unitree-Go2-Play-v0")
    p_one.add_argument("--checkpoint", default="logs/rsl_rl/unitree_go2_rough/2026-03-28_08-36-21/model_2600.pt")
    p_one.add_argument("--num-envs", type=int, default=32)
    p_one.add_argument("--no-video", action="store_true")
    p_one.add_argument("--video-length", type=int, default=800)
    p_one.add_argument("--container", default=DEFAULT_CONTAINER_NAME)
    p_one.set_defaults(func=None)

    args = parser.parse_args()

    if args.cmd == "map-path":
        if args.to_host:
            print(container_to_host_path(args.path))
        else:
            print(host_to_container_path(args.path))
        return

    if args.cmd == "play-cmd":
        need_cam = args.video or args.enable_cameras
        print_play_command(
            task=args.task,
            checkpoint_rel=args.checkpoint,
            num_envs=args.num_envs,
            video=args.video,
            video_length=args.video_length,
            enable_cameras=need_cam,
        )
        return

    if args.cmd == "play-docker":
        print_docker_exec_play_one_liner(
            task=args.task,
            checkpoint_rel=args.checkpoint,
            num_envs=args.num_envs,
            video=not args.no_video,
            video_length=args.video_length,
            container_name=args.container,
        )
        return

    args.func(args)


if __name__ == "__main__":
    main()
