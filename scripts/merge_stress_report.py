#!/usr/bin/env python3
"""Build docs/STRESS_REPORT.md from artifacts/*/metrics_play.json (+ METADATA.txt)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--artifacts-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "artifacts",
        help="Folder containing stress_* / MY_FIRST_REPORT subdirs",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "docs" / "STRESS_REPORT.md",
    )
    args = p.parse_args()
    root: Path = args.artifacts_root

    rows: list[dict] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        mj = d / "metrics_play.json"
        if not mj.is_file():
            continue
        data = json.loads(mj.read_text(encoding="utf-8"))
        meta = {}
        mt = d / "METADATA.txt"
        if mt.is_file():
            for line in mt.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith(" "):
                    k, _, v = line.partition("=")
                    meta[k.strip()] = v.strip()

        ex = data.get("extras_log_latest") or {}
        rows.append(
            {
                "folder": d.name,
                "mean_r": data.get("mean_reward_per_step"),
                "steps": data.get("num_env_steps"),
                "dones": data.get("total_done_events"),
                "err_xy": ex.get("Metrics/base_velocity/error_vel_xy"),
                "err_yaw": ex.get("Metrics/base_velocity/error_vel_yaw"),
                "extra_hydra": meta.get("extra_hydra", ""),
            }
        )

    if not rows:
        print("No metrics_play.json found under", root)
        return

    lines = [
        "# Stress / play eval summary",
        "",
        "Auto-generated from `artifacts/*/metrics_play.json`. Re-run: `python3 scripts/merge_stress_report.py`.",
        "",
        "| Run folder | Steps | Mean reward/step | Total dones | err_vel_xy† | err_vel_yaw† | Hydra overrides (from METADATA) |",
        "|------------|------:|-----------------:|------------:|------------:|-------------:|----------------------------------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['folder']} | {r['steps']} | {r['mean_r']:.4f} | {r['dones']} | "
            f"{_fmt(r['err_xy'])} | {_fmt(r['err_yaw'])} | `{_short(r['extra_hydra'], 80)}` |"
        )
    lines.extend(
        [
            "",
            "† From last `extras['log']` snapshot during the rollout (often updated around env resets); may be empty for very short clips.",
            "",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output} ({len(rows)} runs)")


def _fmt(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{x:.4f}"


def _short(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 3] + "..."


if __name__ == "__main__":
    main()
