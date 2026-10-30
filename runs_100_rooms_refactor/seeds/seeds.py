"""Throwaway tools for choosing the starting houses (seeds) of the 70-to-100-room study. Nothing here is reported.

    python -m adhoc.seeds grow [--out adhoc/seeds]  budget seeds: each priced-run chain's last house grown to 70 rooms
    python -m adhoc.seeds grow --planned            planned seeds: the same houses grown to 70 rooms, every five rooms
                                                    three by the global simulator, one by the local, one at random
    python -m adhoc.seeds judge FILE...             each seed finished to 100 rooms 10 times by every simulator; how
                                                    spread out the finished houses' scores are

Four simulators add rooms to a house one at a time. They all choose from the same list of changes, and none
demolishes the house:
  add next to the house   the room on an empty cell next to an existing room, with a door between the two
  make room with a hallway   an existing room (not the living room) becomes a hallway with a door to each neighbour;
                             that room moves to an empty cell beside it and the new room goes on another, both with
                             a door to the hallway
They differ in how they choose:
  optimizes locally    the best change scored only over its vicinity (the rooms within two cells of it)
  optimizes globally   the best change scored over the whole house
  random               any change
  frequencies          the change most like one a recorded agent made: the same kind of change, next to the same
                       type of room, as near the entrance, its cell touching as many rooms
The optimizers rank by the principles in the prompt's order: corridor rooms, then privacy order, then walking
distance, then compactness. Ties are broken at random.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections import deque
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from house.layout_format import format_layout, parse_layout
from house.model import SIDE_ORDER, Cell, Edge, Layout, WallKind, room_id_number
from house.rules import check_rules, door_graph, entrance_rooms
from house.scores import DESTINATIONS, PRIVATE, PUBLIC, _depths, score

INCREMENTAL = Path(__file__).resolve().parents[2] / "incremental"
FREE_RUN = INCREMENTAL / "runs"
PRICED_RUNS = (INCREMENTAL / "runs_cost_hallways", INCREMENTAL / "runs_cost_hallways_2")
PATCHES = "BCDEFGH"
SIZE = 15
SEED_ROOMS = 70
FINAL_ROOMS = 100
TRIES = 10                          # per simulator, when judging a seed
VICINITY = 2                        # cells
Key = Tuple[float, float, float, float]


# ---- houses ----------------------------------------------------------------------------------------------------

def key(layout: Layout) -> Key:
    s = score(layout)
    return (s.corridor_rooms, s.privacy_order, s.walking_distance, s.compactness)


def around(cell: Cell) -> List[Cell]:
    return [n for n in (cell.neighbour(side) for side in SIDE_ORDER) if n]


def blocked(layout: Layout) -> Set[Cell]:
    """The cells in front of an outer door: a room there would close the entrance."""
    cells = set()
    for door in layout.doors:
        if layout.wall_kind(door) is WallKind.OUTER:
            cells.update(c for c in door.cells() if c and not layout.room_at(c))
    return cells


def free_beside(layout: Layout, cell: Cell, stop: Set[Cell]) -> List[Cell]:
    return [n for n in around(cell)
            if n.row < layout.size and n.col < layout.size and not layout.room_at(n) and n not in stop]


def new_id(layout: Layout, offset: int = 0) -> str:
    return "R%d" % (max(room_id_number(rid) for rid in layout.rooms) + 1 + offset)


def depths(layout: Layout) -> Dict[str, int]:
    return _depths(door_graph(layout), entrance_rooms(layout), banned=None)


def counts(layout: Layout) -> Dict[str, int]:
    found: Dict[str, int] = {}
    for room in layout.rooms.values():
        if room.type != "hallway":
            found[room.type] = found.get(room.type, 0) + 1
    return found


def rooms_to_add(layout: Layout, total: int) -> List[str]:
    """Bedrooms and bathrooms, each time the type the house has fewer of (bedroom on a tie)."""
    have = counts(layout)
    beds, baths = have.get("bedroom", 0), have.get("bathroom", 0)
    added = []
    for _ in range(total - sum(have.values())):
        room_type = "bathroom" if baths < beds else "bedroom"
        beds, baths = beds + (room_type == "bedroom"), baths + (room_type == "bathroom")
        added.append(room_type)
    return added


def on_grid(layout: Layout, size: int) -> Layout:
    """The same rooms and doors on a bigger grid (the windows are left out: no score sees them)."""
    bigger = Layout(size)
    for room in layout.rooms.values():
        bigger.place(room.id, room.type, room.cell)
    for door in layout.doors:
        bigger.add_door(door)
    return bigger


def char_map(layout: Layout) -> List[str]:
    mark = {"living room": "L", "kitchen": "K", "bedroom": "b", "bathroom": "t", "hallway": "="}
    at = {r.cell: mark[r.type] for r in layout.rooms.values()}
    rows, cols = max(c.row for c in at) + 1, max(c.col for c in at) + 1
    return ["".join(at.get(Cell(r, c), ".") for c in range(cols)) for r in range(rows)]


# ---- the list of changes ---------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Change:
    kind: str                       # "add" (next to the house) or "hallway" (make room with a hallway)
    room_type: str                  # the new room
    cell: Cell                      # where the new room goes
    next_to: str                    # add: the room it opens onto; hallway: the room that becomes the hallway
    keep_at: Optional[Cell] = None  # hallway: where that room moves


def changes(layout: Layout, room_type: str) -> List[Change]:
    stop = blocked(layout)
    found = []
    for room in layout.rooms.values():
        free = free_beside(layout, room.cell, stop)
        found += [Change("add", room_type, cell, room.id) for cell in free]
        if room.type != "living room":
            found += [Change("hallway", room_type, cell, room.id, keep_at)
                      for keep_at in free for cell in free if cell != keep_at]
    return found


def apply(layout: Layout, change: Change) -> Layout:
    house = layout.copy()
    anchor = layout.rooms[change.next_to]
    if change.kind == "add":
        house.place(new_id(layout), change.room_type, change.cell)
        house.add_door(Edge.between(change.cell, anchor.cell))
        return house
    house.remove(anchor.id)
    house.place(new_id(layout), "hallway", anchor.cell)
    house.place(anchor.id, anchor.type, change.keep_at)
    house.place(new_id(layout, 1), change.room_type, change.cell)
    for n in around(anchor.cell):
        if house.room_at(n):
            house.add_door(Edge.between(anchor.cell, n))
    return house


def changed_cells(layout: Layout, change: Change) -> Set[Cell]:
    if change.kind == "add":
        return {change.cell}
    return {change.cell, change.keep_at, layout.rooms[change.next_to].cell}


def touches(layout: Layout, change: Change) -> int:
    """How many rooms the new room's cell touches once the change is made."""
    return sum(1 for n in around(change.cell) if layout.room_at(n) or n == change.keep_at)


# ---- scores over a vicinity --------------------------------------------------------------------------------------

def vicinity_key(layout: Layout, cells: Set[Cell]) -> Key:
    """The four scores counted only over the rooms within VICINITY cells of `cells` (routes still run through the
    whole house)."""
    near = [rid for rid, r in layout.rooms.items()
            if any(abs(r.cell.row - c.row) + abs(r.cell.col - c.col) <= VICINITY for c in cells)]
    graph, starts = door_graph(layout), entrance_rooms(layout)
    depth = _depths(graph, starts, banned=None)
    corridor = 0
    for rid in near:
        if layout.rooms[rid].type in DESTINATIONS:
            without = _depths(graph, starts, banned=rid)
            corridor += sum(1 for other in near if other != rid and other in depth and other not in without)
    public = [depth[r] for r in near if layout.rooms[r].type in PUBLIC]
    private = [depth[r] for r in near if layout.rooms[r].type in PRIVATE]
    wrong = sum(1.0 if q < p else 0.5 if q == p else 0.0 for p in public for q in private)
    privacy = wrong / (len(public) * len(private)) if public and private else 0.0
    total = pairs = 0
    for i, rid in enumerate(near):
        distance = _depths(graph, [rid], banned=None)
        for other in near[i + 1:]:
            total += distance[other]
            pairs += 1
    walking = total / pairs if pairs else 0.0
    outer = sum(1 for rid in near for e in layout.rooms[rid].edges() if layout.wall_kind(e) is WallKind.OUTER)
    return (corridor, privacy, walking, outer - 2 * math.ceil(2 * math.sqrt(len(near))))


def local_effect(layout: Layout, change: Change) -> Key:
    """What the change does to its vicinity: the vicinity's scores after it, less the same area's before."""
    cells = changed_cells(layout, change)
    after, before = vicinity_key(apply(layout, change), cells), vicinity_key(layout, cells)
    return tuple(a - b for a, b in zip(after, before))


# ---- the simulators ----------------------------------------------------------------------------------------------

def best(options: List[Change], rank: Callable[[Change], Key], rng: random.Random) -> Change:
    ranked = [(rank(c), c) for c in options]
    top = min(k for k, _ in ranked)
    return rng.choice([c for k, c in ranked if k == top])


def optimizes_locally(layout: Layout, room_type: str, rng: random.Random) -> Layout:
    return apply(layout, best(changes(layout, room_type), lambda c: local_effect(layout, c), rng))


def optimizes_globally(layout: Layout, room_type: str, rng: random.Random) -> Layout:
    return apply(layout, best(changes(layout, room_type), lambda c: key(apply(layout, c)), rng))


def random_change(layout: Layout, room_type: str, rng: random.Random) -> Layout:
    return apply(layout, rng.choice(changes(layout, room_type)))


@dataclass(frozen=True)
class Observed:
    """What one recorded agent did with one new room."""
    new_type: str
    kind: str                       # add, hallway or rebuild
    next_to_type: Optional[str]     # the type of the room it built next to, or made into the hallway
    nearer: Optional[float]         # share of the rooms with an empty cell beside them nearer the entrance than that
    touches: Optional[int]          # how many rooms the new room's cell touches afterwards


def nearer_share(layout: Layout, rid: str, depth: Dict[str, int], sided: Sequence[str]) -> float:
    return sum(depth[s] < depth[rid] for s in sided) / len(sided)


def sided_rooms(layout: Layout) -> List[str]:
    stop = blocked(layout)
    return [rid for rid, room in layout.rooms.items() if free_beside(layout, room.cell, stop)]


def frequencies(layout: Layout, room_type: str, rng: random.Random, observed: Sequence[Observed]) -> Layout:
    seen = rng.choice([o for o in observed if o.new_type == room_type and o.kind != "rebuild"])
    depth, sided = depths(layout), sided_rooms(layout)
    options = [c for c in changes(layout, room_type) if c.kind == seen.kind] or changes(layout, room_type)
    likeness = lambda c: (layout.rooms[c.next_to].type != seen.next_to_type,
                          abs(nearer_share(layout, c.next_to, depth, sided) - seen.nearer),
                          abs(touches(layout, c) - seen.touches))
    return apply(layout, best(options, likeness, rng))


def grow(layout: Layout, room_types: Sequence[str], add_room, rng: random.Random) -> Layout:
    for room_type in room_types:
        layout = add_room(layout, room_type, rng)
    assert not check_rules(layout)
    return layout


# ---- the recorded steps ------------------------------------------------------------------------------------------

@dataclass
class Step:
    start: Layout
    new_type: str
    end: Layout


def final_houses(run_dir: Path) -> Dict[str, dict]:
    """The last valid house of each step: the one carried on to the next."""
    houses: Dict[str, dict] = {}
    for path in sorted(run_dir.glob("run_*.json")):
        record = json.loads(path.read_text())
        if record["accepted"] and record["valid"]:
            houses[record["label"]] = record
    return houses


def recorded_steps(run_dir: Path) -> List[Step]:
    houses = final_houses(run_dir)
    return [Step(parse_layout(houses[label[:-1] + chr(ord(label[-1]) - 1)]["layout"]),
                 record["request"].split(": ")[1], parse_layout(record["layout"]))
            for label, record in sorted(houses.items()) if label[-1] in PATCHES]


def describe(step: Step) -> Observed:
    start, end = step.start, step.end
    changed = [rid for rid, room in start.rooms.items()
               if rid not in end.rooms or end.rooms[rid].cell != room.cell or end.rooms[rid].type != room.type]
    if 2 * len(changed) >= len(start.rooms):
        return Observed(step.new_type, "rebuild", None, None, None)
    depth, sided = depths(start), sided_rooms(start)
    new = [rid for rid in end.rooms if rid not in start.rooms and end.rooms[rid].type == step.new_type][-1]
    touching = sum(1 for n in around(end.rooms[new].cell) if end.room_at(n))
    if changed:
        now = {rid: end.room_at(start.rooms[rid].cell) for rid in changed}
        rid = ([r for r in changed if now[r] and now[r].type == "hallway"] or changed)[0]   # the room made a hallway
        return Observed(step.new_type, "hallway", start.rooms[rid].type,
                        nearer_share(start, rid, depth, sided), touching)
    graph = door_graph(end)
    seen, queue, anchors = {new}, deque([new]), []
    while queue:                    # through any new hallway, to the old rooms the new room was joined to
        for nxt in graph[queue.popleft()]:
            if nxt not in seen:
                seen.add(nxt)
                (anchors.append if nxt in start.rooms else queue.append)(nxt)
    rid = min(anchors, key=lambda r: depth[r])
    return Observed(step.new_type, "add", start.rooms[rid].type, nearer_share(start, rid, depth, sided), touching)


def observed(run_dirs: Sequence[Path]) -> List[Observed]:
    return [describe(s) for d in run_dirs for s in recorded_steps(d)]


# ---- commands ----------------------------------------------------------------------------------------------------

def mixed(rooms: int, rng: random.Random) -> List[Callable[[Layout, str, random.Random], Layout]]:
    """For every five rooms: three by the global simulator, one by the local one, one at random, in a random order."""
    order: List[Callable[[Layout, str, random.Random], Layout]] = []
    while len(order) < rooms:
        block = [optimizes_globally] * 3 + [optimizes_locally, random_change]
        rng.shuffle(block)
        order += block
    return order[:rooms]


def run_grow(args: argparse.Namespace) -> None:
    seen = observed(PRICED_RUNS)
    args.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    for run_dir in PRICED_RUNS:
        for label, record in sorted(final_houses(run_dir).items()):
            if label.endswith("-H"):
                start = on_grid(parse_layout(record["layout"]), SIZE)
                to_add = rooms_to_add(start, SEED_ROOMS)
                if args.planned:
                    steps = iter(mixed(len(to_add), rng))
                    house = grow(start, to_add, lambda h, t, r: next(steps)(h, t, r), rng)
                else:
                    house = grow(start, to_add, lambda h, t, r: frequencies(h, t, r, seen), rng)
                name = "%s-%s-%s.txt" % ("planned" if args.planned else "budget", run_dir.name.replace("runs_", ""),
                                         label.split("-")[2])
                (args.out / name).write_text(format_layout(house))
                print(name)
                print("\n".join("    " + line for line in char_map(house)))


def finish(path: str) -> Dict[str, List[Key]]:
    """The scores of the seed finished to FINAL_ROOMS rooms, TRIES times by each simulator."""
    seed = parse_layout(Path(path).read_text())
    to_add = rooms_to_add(seed, FINAL_ROOMS)
    seen = observed([FREE_RUN])
    simulators = {"optimizes locally": optimizes_locally, "optimizes globally": optimizes_globally,
                  "random": random_change, "frequencies": lambda h, t, r: frequencies(h, t, r, seen)}
    return {name: [key(grow(seed, to_add, add, random.Random("%s %s %d" % (path, name, i)))) for i in range(TRIES)]
            for name, add in simulators.items()}


def run_judge(args: argparse.Namespace) -> None:
    files = sorted(args.files)
    with Pool(len(files)) as pool:
        finished = dict(zip(files, pool.map(finish, files)))
    Path(args.out).write_text(json.dumps(finished, indent=1))
    rows = [("house", "corridor rooms", "privacy order", "walking distance", "compactness")]
    for number, path in enumerate(files, start=1):
        keys = [k for ks in finished[path].values() for k in ks]
        rows.append(("%d" % number, *(fmt % statistics.stdev(k[i] for k in keys)
                                      for i, fmt in enumerate(("%.1f", "%.4f", "%.2f", "%.1f")))))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    print("\n".join("  ".join(c.rjust(w) for c, w in zip(r, widths)) for r in rows))


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Throwaway tools for choosing seed houses")
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("grow")
    g.add_argument("--out", type=Path, default=Path("adhoc/seeds"))
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--planned", action="store_true")
    j = sub.add_parser("judge")
    j.add_argument("files", nargs="+")
    j.add_argument("--out", default="adhoc/seeds/judge.json", help="every finished house's scores")
    args = parser.parse_args(argv)
    {"grow": run_grow, "judge": run_judge}[args.command](args)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
