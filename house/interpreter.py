"""Run a script against a layout, command by command.

Policy: if any line fails to parse, or any command cannot be carried out, the whole script is
rejected and the house stays as it was. Everything else is built, even if it breaks the rules.
Removing and replacing are free; nothing is priced.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .commands import (
    AddDoor, AddNextTo, AddWall, AddWindow, Command, PlaceRoom, RemoveDoor, RemoveRoom,
    RemoveTyped, RemoveWall, RemoveWindow, parse_script,
)
from .model import (
    SIDE_ORDER, Cell, Edge, Layout, Room, WallKind, edge_description, room_id_number,
)
from .rules import Violation, check_requested_rooms, check_rules
from .scores import Scores, score


class CommandError(Exception):
    """A command that cannot be carried out on the house as it stands."""


@dataclass(frozen=True)
class Executed:
    number: int                         # script line number
    command: Command
    expansion: Tuple[Command, ...]      # the primitives it ran as (just itself for a primitive)


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
    executed: List[Executed] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    command_count: int = 0                          # commands in the script, as written

    @property
    def valid(self) -> bool:
        return not self.violations

    @property
    def scores(self) -> Optional[Scores]:
        """None unless the house is valid."""
        return score(self.layout) if self.valid else None


def run_script(script: str, start: Optional[Layout] = None, request: Optional[str] = None) -> RunResult:
    layout = (start or Layout()).copy()
    lines = parse_script(script)
    count = len(lines)

    parse_errors = [ScriptError(l.number, l.text, l.error or "") for l in lines if l.command is None]
    if parse_errors:
        return _rejected(start, parse_errors, count)

    executed: List[Executed] = []
    violations: List[Violation] = []
    for line in lines:
        assert line.command is not None
        try:
            expansion = expand(line.command, layout)
            for primitive in expansion:
                violations += _apply(layout, primitive)
        except CommandError as e:
            return _rejected(start, [ScriptError(line.number, line.text, str(e))], count)
        executed.append(Executed(line.number, line.command, expansion))

    violations += check_requested_rooms(start or Layout(), layout, request)
    return RunResult(layout, True, [], executed, check_rules(layout) + violations, count)


def _rejected(start: Optional[Layout], errors: List[ScriptError], count: int) -> RunResult:
    layout = (start or Layout()).copy()
    return RunResult(layout, False, errors, [], check_rules(layout), count)


# ---------------------------------------------------------------- composites

def expand(command: Command, layout: Layout) -> Tuple[Command, ...]:
    """Composite commands become primitives, decided by the house as it stands; primitives stay as they are."""
    if isinstance(command, AddNextTo):
        target = layout.rooms.get(command.target)
        if target is None:
            raise CommandError("there is no room %s to put the %s next to" % (command.target, command.room_type))
        owner = layout.cell_map()
        options = sorted(
            (free, cell) for cell in target.cells for free in cell.neighbours() if free not in owner
        )
        if not options:
            raise CommandError("%s has no free cell next to it" % command.target)
        free, beside = options[0]    # first free cell in A1..D4 order, and the target cell it touches
        return (
            PlaceRoom(_next_id(layout), command.room_type, free),
            AddDoor(Edge.between(beside, free)),
        )
    if isinstance(command, RemoveTyped):
        room = layout.rooms.get(command.room_id)
        if room is None or room.type != command.room_type:
            raise CommandError("%s is not a %s" % (command.room_id, command.room_type))
        return (RemoveRoom(command.room_id),)
    return (command,)


def _next_id(layout: Layout) -> str:
    n = 1
    while "R%d" % n in layout.rooms:
        n += 1
    return "R%d" % n


# ---------------------------------------------------------------- primitives

def _apply(layout: Layout, c: Command) -> List[Violation]:
    if isinstance(c, PlaceRoom):
        return _place(layout, c)
    if isinstance(c, RemoveRoom):
        return _remove_room(layout, c)
    if isinstance(c, AddWall):
        return _wall(layout, c)
    if isinstance(c, RemoveWall):
        return _remove_wall(layout, c)
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
        raise CommandError("%s is not a primitive" % c)
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


def _wall(layout: Layout, c: AddWall) -> List[Violation]:
    return []                   # every room already has walls all around it, so there is nothing to add


def _remove_wall(layout: Layout, c: RemoveWall) -> List[Violation]:
    a, b = layout.sides(c.edge)
    if a and b and a != b:
        raise CommandError("the wall %s between %s and %s cannot be removed: rooms are never joined"
                           % (edge_description(c.edge), a, b))
    return []                   # no wall between two rooms there, nothing to remove
