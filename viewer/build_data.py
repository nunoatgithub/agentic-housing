"""Export a run folder as one JSON file the 3D viewer can play.

    python viewer/build_data.py [runs_100_rooms_no_hallways] [-o viewer/data.json]

Each house chain becomes a list of frames: the seed house, then the house left by every accepted, valid one-room
step (step01, step02, ...). The allNN calls are side branches that each start from the house left by the step before
them; they are kept as frames too and the viewer shows them as a separate all-at-once sequence. Failed tries are skipped. Every step frame keeps its full run label in `tag` (model-effort-hH-cC-call); the viewer parses it to separate chains. A frame holds rooms (id, type, row, col) and the doors between them.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from house.layout_format import parse_layout as parse_full
from house import model
from house.scores import score

model.set_grid_size(15)


def parse_layout(text: str) -> dict:
    section = None
    rooms, doors = [], []
    for line in text.splitlines():
        s = line.strip()
        if s in ("rooms", "doors", "windows"):
            section = s
            continue
        if section == "rooms":
            m = re.match(r"(R\d+)\s+([a-z]+(?: room)?)\s+([A-Z])(\d+)$", s)
            if m:
                rooms.append({"id": m[1], "type": m[2].replace(" room", ""), "r": ord(m[3]) - 65, "c": int(m[4]) - 1})
        elif section == "doors" and "|" in s:
            a, b = s.split("|")
            doors.append([a.strip(), b.split()[0]])
    return {"rooms": rooms, "doors": doors}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="?", default="runs_100_rooms_no_hallways")
    ap.add_argument("-o", "--out", default="viewer/data.json")
    args = ap.parse_args()
    runs = Path(args.runs)

    houses: dict[int, list] = {}
    for n in range(1, 5):
        seed = runs / "seeds" / f"house{n}.txt"
        if seed.exists():
            sc = score(parse_full(seed.read_text()))
            houses[n] = [{"label": f"seed house {n}", "call": "seed", "scores": vars(sc) if sc else None, **parse_layout(seed.read_text())}]

    for f in sorted(runs.glob("run_*.json")):
        d = json.loads(f.read_text())
        m = re.search(r"-h(\d)-c\d+-(\w+)$", d.get("label", ""))
        if not m or not m[2].startswith(("step", "all")) or not (d.get("accepted") and d.get("valid")):
            continue
        frame = {"label": d["run_id"], "tag": d["label"], "call": m[2], "request": d.get("request", ""), "scores": d.get("scores"), **parse_layout(d["layout"])}
        houses.setdefault(int(m[1]), []).append(frame)

    out = {"source": runs.name, "grid": 15, "houses": {str(k): v for k, v in sorted(houses.items())}}
    Path(args.out).write_text(json.dumps(out, separators=(",", ":")))
    for k, v in sorted(houses.items()):
        print(f"house {k}: {len(v)} frames, {len(v[-1]['rooms'])} rooms at the end")


if __name__ == "__main__":
    main()
