"""The four quality scores. Reported separately, never combined; only defined for valid houses.

corridor_rooms    pairs (kitchen/bedroom/bathroom X, room D) where every route from the entrance to D passes X. 0 is best.
privacy_order     share of (public, private) room pairs in the wrong order; a tie counts half. 0 is best.
walking_distance  mean number of doors between every pair of rooms (shortest way). Lower is better.
compactness       outer-wall edges beyond the minimum possible for that many cells. 0 is best.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set

from .model import Layout, WallKind, all_edges
from .rules import check_rules, door_graph, entrance_rooms

PUBLIC = ("living room", "kitchen")
PRIVATE = ("bedroom", "bathroom")
DESTINATIONS = ("kitchen", "bedroom", "bathroom")     # rooms nobody should have to walk through


@dataclass(frozen=True)
class Scores:
    corridor_rooms: int
    privacy_order: float
    walking_distance: float
    compactness: int


def score(layout: Layout) -> Optional[Scores]:
    """None if the house breaks any rule."""
    if check_rules(layout):
        return None
    graph = door_graph(layout)
    starts = entrance_rooms(layout)
    depth = _depths(graph, starts, banned=None)
    return Scores(
        corridor_rooms=_corridor_rooms(layout, graph, starts, depth),
        privacy_order=_privacy_order(layout, depth),
        walking_distance=_walking_distance(graph),
        compactness=_compactness(layout),
    )


def _depths(graph: Dict[str, Set[str]], starts: Iterable[str], banned: Optional[str]) -> Dict[str, int]:
    """Doors from the nearest entrance room to every room reachable without passing `banned`."""
    depth = {s: 0 for s in starts if s != banned}
    queue = deque(depth)
    while queue:
        room = queue.popleft()
        for nxt in graph[room]:
            if nxt != banned and nxt not in depth:
                depth[nxt] = depth[room] + 1
                queue.append(nxt)
    return depth


def _walking_distance(graph: Dict[str, Set[str]]) -> float:
    """Average, over all pairs of rooms, of the fewest doors between them. 0 for a house of one room."""
    rooms = list(graph)
    total = pairs = 0
    for i, room in enumerate(rooms):
        distance = _depths(graph, [room], banned=None)
        for other in rooms[i + 1:]:
            total += distance[other]
            pairs += 1
    return round(total / pairs, 4) if pairs else 0.0


def _corridor_rooms(layout: Layout, graph: Dict[str, Set[str]], starts: List[str], depth: Dict[str, int]) -> int:
    total = 0
    for rid, room in layout.rooms.items():
        if room.type in DESTINATIONS:
            without = _depths(graph, starts, banned=rid)
            total += sum(1 for other in depth if other != rid and other not in without)
    return total


def _privacy_order(layout: Layout, depth: Dict[str, int]) -> float:
    public = [depth[r] for r in depth if layout.rooms[r].type in PUBLIC]
    private = [depth[r] for r in depth if layout.rooms[r].type in PRIVATE]
    pairs = len(public) * len(private)
    if not pairs:
        return 0.0
    wrong = sum(1.0 if q < p else 0.5 if q == p else 0.0 for p in public for q in private)
    return round(wrong / pairs, 4)


def _compactness(layout: Layout) -> int:
    cells = sum(len(r.cells) for r in layout.rooms.values())
    outer = sum(1 for e in all_edges() if layout.wall_kind(e) is WallKind.OUTER)
    return outer - 2 * math.ceil(2 * math.sqrt(cells))
