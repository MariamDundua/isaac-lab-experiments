#!/usr/bin/env python3
"""Export last scalar values from a TensorBoard run directory (one events file is enough)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tensorboard.backend.event_processing import event_accumulator


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "logdir",
        type=Path,
        help="Directory containing events.out.tfevents.* (e.g. training run folder)",
    )
    p.add_argument("-o", "--output", type=Path, help="Write JSON here (default: stdout)")
    args = p.parse_args()
    logdir = args.logdir.resolve()
    if not logdir.is_dir():
        raise SystemExit(f"Not a directory: {logdir}")

    acc = event_accumulator.EventAccumulator(str(logdir), size_guidance={event_accumulator.SCALARS: 0})
    acc.Reload()
    tags = acc.Tags().get("scalars") or []
    out: dict[str, dict] = {}
    for tag in tags:
        events = acc.Scalars(tag)
        if not events:
            continue
        last = events[-1]
        out[tag] = {"step": last.step, "value": float(last.value)}

    payload = {"logdir": str(logdir), "num_scalars": len(out), "scalars": out}
    text = json.dumps(payload, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"Wrote {args.output} ({len(out)} tags)")
    else:
        print(text)


if __name__ == "__main__":
    main()
