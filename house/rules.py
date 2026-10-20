"""The hard rules (validity). Reported, never enforced: a house that breaks rules is still built."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Set

from .model import ROOM_TYPES, SIDE_ORDER, Edge, Layout, WallKind, room_id_number
from .requests import parse_request

CIRCULATION = "circulation"
NO_DETACHED_ROOMS = "no detached rooms"
EVERY_ROOM_HAS_A_DOOR = "every room has a door"
ONE_ENTRANCE = "one entrance"
ONE_KITCHEN = "one kitchen"
REQUESTED_ROOMS = "requested rooms"

RULE_NUMBERS = {
    CIRCULATION: 1,
    NO_DETACHED_ROOMS: 2,
    EVERY_ROOM_HAS_A_DOOR: 3,
    ONE_ENTRANCE: 4,
    ONE_KITCHEN: 5,
    REQUESTED_ROOMS: 6,
}


@dataclass(frozen=True)
class Violation:
    rule: str       # one of the names above
    message: str

    @property
    def number(self) -> int:
        return RULE_NUMBERS[self.rule]

    def __str__(self) -> str:
        return "rule %d (%s): %s" % (self.number, self.rule, self.message)


def check_requested_rooms(before: Layout, after: Layout, request: Optional[str]) -> List[Violation]:
    """The finished house must have exactly the number of rooms the request asked for.

    'build': each room type listed, exactly that many. 'add': the rooms the house started with, plus the ones
    asked for. Hallways are free unless the request names them. No request (or one this does not understand)
    means nothing to check.
    """
    parsed = parse_request(request)
    if not parsed:
        return []
    kind, asked = parsed
    count = lambda layout, t: sum(1 for r in layout.rooms.values() if r.type == t)
    violations = []
    for t in ROOM_TYPES:
        if t == "hallway" and t not in asked:
            continue
        need = count(before, t) + asked.get(t, 0) if kind == "add" else asked.get(t)
        if need is None or count(after, t) == need:
            continue
        violations.append(Violation(
            REQUESTED_ROOMS, "'%s' needs %d %s but the house has %d" % (request, need, t, count(after, t))))
    return violations


def door_graph(layout: Layout) -> Dict[str, Set[str]]:
    """Room id -> ids of rooms joined to it by a door. Outer doors are not in the graph."""
    graph: Dict[str, Set[str]] = {rid: set() for rid in layout.rooms}
    for door in layout.doors:
        a, b = layout.sides(door)
        if a and b and a != b:
            graph[a].add(b)
            graph[b].add(a)
    return graph


def entrance_rooms(layout: Layout) -> List[str]:
    """Living rooms that have a door in an outer wall: where a person walking in arrives."""
    found = set()
    for door in layout.doors:
        if layout.wall_kind(door) is WallKind.OUTER:
            a, b = layout.sides(door)
            rid = a or b
            if rid and layout.rooms[rid].type == "living room":
                found.add(rid)
    return sorted(found, key=room_id_number)


def check_rules(layout: Layout) -> List[Violation]:
    """All the rules on this house; an empty list means it is valid."""
    violations: List[Violation] = []
    ids = sorted(layout.rooms, key=room_id_number)
    graph = door_graph(layout)

    def label(rid: str) -> str:
        return "%s (%s)" % (rid, layout.rooms[rid].type)

    # Rule 4: one entrance
    if not any(r.type == "living room" for r in layout.rooms.values()):
        violations.append(Violation(ONE_ENTRANCE, "the house has no living room"))
    for door in sorted(layout.doors, key=lambda e: (e.horizontal, e.row, e.col)):
        if layout.wall_kind(door) is WallKind.OUTER:
            a, b = layout.sides(door)
            rid = a or b
            if layout.rooms[rid].type != "living room":
                violations.append(Violation(
                    ONE_ENTRANCE, "%s has a door in an outer wall; only the living room may" % label(rid)))

    # Rule 5: never more than one kitchen
    kitchens = [rid for rid in ids if layout.rooms[rid].type == "kitchen"]
    if len(kitchens) > 1:
        violations.append(Violation(
            ONE_KITCHEN, "the house has %d kitchens (%s); at most one is allowed" % (len(kitchens), ", ".join(kitchens))))

    # Rule 1: circulation
    starts = entrance_rooms(layout)
    reached: Set[str] = set(starts)
    queue = deque(starts)
    while queue:
        for nxt in sorted(graph[queue.popleft()], key=room_id_number):
            if nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)
    if ids and not starts:
        violations.append(Violation(CIRCULATION, "there is no entrance: no living room has a door in an outer wall"))
    for rid in ids:
        if rid not in reached and starts:
            violations.append(Violation(CIRCULATION, "%s cannot be reached from the entrance through doors" % label(rid)))

    if len(ids) > 1:
        # Rule 2: no detached rooms
        for rid in ids:
            if not any(layout.wall_kind(e) is WallKind.INNER for e in _room_edges(layout, rid)):
                violations.append(Violation(NO_DETACHED_ROOMS, "%s shares no wall with any other room" % label(rid)))
        # Rule 3: every room has a door shared with a neighbouring room
        for rid in ids:
            if not graph[rid]:
                violations.append(Violation(EVERY_ROOM_HAS_A_DOOR, "%s has no door to a neighbouring room" % label(rid)))
    return violations


def _room_edges(layout: Layout, rid: str) -> Iterator[Edge]:
    for cell in layout.rooms[rid].cells:
        for side in SIDE_ORDER:
            yield Edge.of(cell, side)
