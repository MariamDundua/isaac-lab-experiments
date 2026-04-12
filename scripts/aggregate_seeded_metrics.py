#!/usr/bin/env python3
"""Summarize mean_reward_per_step across seeds for artifacts matching imp_*_seed<N>/metrics_play.json."""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent / "artifacts"
    pat = re.compile(r"^(?P<base>.+)_seed(?P<seed>\d+)$")
    groups: dict[str, list[tuple[int, float]]] = {}
    for d in sorted(root.iterdir()):
        if not d.is_dir() or not d.name.startswith("imp_"):
            continue
        m = pat.match(d.name)
        if not m:
            continue
        mj = d / "metrics_play.json"
        if not mj.is_file():
            continue
        data = json.loads(mj.read_text(encoding="utf-8"))
        r = data.get("mean_reward_per_step")
        if r is None:
            continue
        base = m.group("base")
        seed = int(m.group("seed"))
        groups.setdefault(base, []).append((seed, float(r)))

    if not groups:
        print("No imp_*_seed*/metrics_play.json found under", root)
        print(
            "Hint: if you have imp_* folders with only METADATA/videos, Isaac may have "
            "exited during shutdown before metrics were written. Use the latest "
            "play_eval_metrics.py (writes JSON before env.close), then re-run "
            "stress_test_seeded.sh or individual play_and_collect.sh jobs."
        )
        return

    lines = [
        "# Seeded runs — mean reward/step summary",
        "",
        "| Regime (prefix) | n | mean | stdev | min | max | seeds |",
        "|-----------------|--:|-----:|------:|----:|----:|-------|",
    ]
    for base in sorted(groups.keys()):
        pts = sorted(groups[base], key=lambda x: x[0])
        vals = [v for _, v in pts]
        seeds = ",".join(str(s) for s, _ in pts)
        lines.append(
            f"| {base} | {len(vals)} | {statistics.mean(vals):.4f} | "
            f"{statistics.stdev(vals) if len(vals) > 1 else 0.0:.4f} | "
            f"{min(vals):.4f} | {max(vals):.4f} | `{seeds}` |"
        )
    out = Path(__file__).resolve().parent.parent / "docs" / "SEEDED_SUMMARY.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
