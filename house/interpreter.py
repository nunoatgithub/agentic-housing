"""Run a script against a layout, command by command.

Policy: if any line fails to parse, or any command cannot be carried out, the whole script is
rejected and the house stays as it was. Everything else is built, even if it breaks the rules.
Removing and replacing are free; nothing is priced.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .commands import AddDoor, AddWindow, Command, PlaceRoom, RemoveDoor, RemoveRoom, RemoveWindow, parse_script, script_cost
from .model import HALLWAY, SIDE_ORDER, Edge, Layout, Room, WallKind, edge_description
from .rules import Violation, check_requested_rooms, check_rules
from .scores import Scores, score


class CommandError(Exception):
    """A command that cannot be carried out on the house as it stands."""


@dataclass(frozen=True)
class ScriptError:
    number: int
    text: str
    reason: str


@dataclass
class RunResult:
    layout: Layout                                  # the house after the script (unchanged if rejected)
    accepted: bool
    errors: List[ScriptError] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    command_count: int = 0                          # commands in the script, as written
    cost: int = 0                                   # what the script costs (commands.PRICES); 0 if it was rejected

    @property
    def valid(self) -> bool:
        return not self.violations

    @property
    def scores(self) -> Optional[Scores]:
        """None unless the house is valid."""
        return score(self.layout) if self.valid else None


def run_script(script: str, start: Optional[Layout] = None, request: Optional[str] = None, hallways: bool = False) -> RunResult:
    """Build a script on a house. Hallways may be built only if the run allows them."""
    layout = (start or Layout()).copy()
    lines = parse_script(script)
    count = len(lines)

    parse_errors = [ScriptError(l.number, l.text, l.error or "") for l in lines if l.command is None]
    if parse_errors:
        return _rejected(start, parse_errors, count)

    violations: List[Violation] = []
    for line in lines:
        assert line.command is not None
        try:
            violations += _apply(layout, line.command, hallways)
        except CommandError as e:
            return _rejected(start, [ScriptError(line.number, line.text, str(e))], count)

    violations += check_requested_rooms(start or Layout(), layout, request)
    return RunResult(layout, True, [], check_rules(layout) + violations, count, script_cost(script))


def _rejected(start: Optional[Layout], errors: List[ScriptError], count: int) -> RunResult:
    layout = (start or Layout()).copy()
    return RunResult(layout, False, errors, check_rules(layout), count)


# ---------------------------------------------------------------- primitives

def _apply(layout: Layout, c: Command, hallways: bool) -> List[Violation]:
    if isinstance(c, PlaceRoom):
        if c.room_type == HALLWAY and not hallways:
            raise CommandError("there are no hallways in this house")
        return _place(layout, c)
    if isinstance(c, RemoveRoom):
        return _remove_room(layout, c)
    if isinstance(c, AddDoor):
        if layout.wall_kind(c.edge) is WallKind.NONE:
            raise CommandError("no wall on %s to put a door in" % edge_description(c.edge))
        layout.doors.add(c.edge)
    elif isinstance(c, RemoveDoor):
        layout.doors.discard(c.edge)
    elif isinstance(c, AddWindow):
        if layout.wall_kind(c.edge) is not WallKind.OUTER:
            raise CommandError("%s is not an outer wall, so it cannot take a window" % edge_description(c.edge))
        layout.windows.add(c.edge)
    elif isinstance(c, RemoveWindow):
        layout.windows.discard(c.edge)
    else:
        raise CommandError("unknown command %s" % c)
    return []


def _place(layout: Layout, c: PlaceRoom) -> List[Violation]:
    if c.room_id in layout.rooms:
        raise CommandError("room id %s is already in use" % c.room_id)
    if layout.room_at(c.cell) is not None:
        raise CommandError("cell %s is already taken by %s" % (c.cell, layout.room_at(c.cell).id))
    layout.rooms[c.room_id] = Room(c.room_id, c.room_type, frozenset({c.cell}))
    # A wall that used to face the outside now faces the new room: what was on it goes.
    for side in SIDE_ORDER:
        n = c.cell.neighbour(side)
        if n is not None and layout.room_at(n) is not None:
            layout.doors.discard(Edge.of(c.cell, side))
            layout.windows.discard(Edge.of(c.cell, side))
    return []


def _remove_room(layout: Layout, c: RemoveRoom) -> List[Violation]:
    room = layout.rooms.get(c.room_id)
    if room is None:
        raise CommandError("there is no room %s" % c.room_id)
    for cell in room.cells:
        for side in SIDE_ORDER:
            layout.doors.discard(Edge.of(cell, side))
            layout.windows.discard(Edge.of(cell, side))
    del layout.rooms[c.room_id]
    return []
