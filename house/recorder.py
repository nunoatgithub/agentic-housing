"""One saved record per POST /script: everything needed to analyse the run later."""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from .interpreter import RunResult
from .layout_format import format_layout
from .render import Drawing, render_house


def build_record(run_id: str, timestamp: str, label: Optional[str],
                 script: str, result: RunResult, request: Optional[str] = None, hallways: bool = False) -> Dict[str, Any]:
    """A plain dict, ready for JSON. A rejected script built nothing, so it has no validity, rules or scores."""
    built = result.accepted
    scores = result.scores if built else None
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "label": label,
        "request": request,
        "hallways": hallways,
        "command_count": result.command_count,
        "accepted": built,
        "errors": [{"line": e.number, "text": e.text, "reason": e.reason} for e in result.errors],
        "script": script,
        "layout": format_layout(result.layout),
        "drawing": render_house(Drawing.of(run_id, result)),
        "valid": result.valid if built else None,
        "violations": [{"rule": v.number, "name": v.rule, "message": v.message} for v in result.violations] if built else [],
        "scores": asdict(scores) if scores else None,
        "cost": result.cost if built else None,
    }


def next_run_id(runs_dir: Path) -> str:
    numbers = [int(m.group(1)) for p in runs_dir.glob("run_*.json") if (m := re.fullmatch(r"run_(\d+)\.json", p.name))]
    return "run_%04d" % (max(numbers, default=0) + 1)


def save_record(runs_dir: Path, record: Dict[str, Any], banner: str = "") -> None:
    """run_NNNN.json holds the record; run_NNNN.txt is the same run to read in a text editor."""
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = record["run_id"]
    (runs_dir / (run_id + ".json")).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    header = "label: %s   at %s   commands: %d\n\n" % (
        record["label"] or "-", record["timestamp"], record["command_count"])
    (runs_dir / (run_id + ".txt")).write_text(
        header + "SCRIPT\n" + record["script"].strip() + "\n\n" + banner + record["drawing"] + "\n")
