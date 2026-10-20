"""The command syntax: command dataclasses and the script parser.

Parsing only checks syntax. Whether a command can be carried out on a given house (a door on an
edge with no wall, a room id already in use, ...) is the interpreter's business, not the parser's.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Union

from .model import (
    ROOM_ID_RE,
    ROOM_TYPES,
    Cell,
    Edge,
    ModelError,
    ParseError,
    edge_description,
    parse_edge,
)


@dataclass(frozen=True)
class PlaceRoom:            # room R6 bedroom C2
    room_id: str
    room_type: str
    cell: Cell

    def __str__(self) -> str:
        return "room %s %s %s" % (self.room_id, self.room_type, self.cell)


@dataclass(frozen=True)
class RemoveRoom:           # remove room R6
    room_id: str

    def __str__(self) -> str:
        return "remove room %s" % self.room_id


@dataclass(frozen=True)
class AddWall:              # wall B2|B3
    edge: Edge

    def __str__(self) -> str:
        return "wall %s" % edge_description(self.edge)


@dataclass(frozen=True)
class RemoveWall:           # remove wall B2|B3
    edge: Edge

    def __str__(self) -> str:
        return "remove wall %s" % edge_description(self.edge)


@dataclass(frozen=True)
class AddDoor:              # door B1|B2
    edge: Edge

    def __str__(self) -> str:
        return "door %s" % edge_description(self.edge)


@dataclass(frozen=True)
class RemoveDoor:           # remove door B1|B2
    edge: Edge

    def __str__(self) -> str:
        return "remove door %s" % edge_description(self.edge)


@dataclass(frozen=True)
class AddWindow:            # window B2|east
    edge: Edge

    def __str__(self) -> str:
        return "window %s" % edge_description(self.edge)


@dataclass(frozen=True)
class RemoveWindow:         # remove window B2|east
    edge: Edge

    def __str__(self) -> str:
        return "remove window %s" % edge_description(self.edge)


@dataclass(frozen=True)
class AddNextTo:            # add bathroom next to R4   (composite)
    room_type: str
    target: str

    def __str__(self) -> str:
        return "add %s next to %s" % (self.room_type, self.target)


@dataclass(frozen=True)
class RemoveTyped:          # remove bathroom R5   (composite)
    room_type: str
    room_id: str

    def __str__(self) -> str:
        return "remove %s %s" % (self.room_type, self.room_id)


Command = Union[
    PlaceRoom, RemoveRoom, AddWall, RemoveWall,
    AddDoor, RemoveDoor, AddWindow, RemoveWindow, AddNextTo, RemoveTyped,
]


@dataclass(frozen=True)
class ScriptLine:
    """One non-blank line of a script: either a parsed command or the reason it could not be parsed."""

    number: int                 # 1-based line number in the script
    text: str                   # the line as written, stripped
    command: Optional[Command]
    error: Optional[str]


_TYPE = "(%s)" % "|".join(re.escape(t) for t in ROOM_TYPES)
_ID = r"(R[1-9][0-9]{0,2})"
_EDGE = r"(\S+)"


def _edge(text: str) -> Edge:
    try:
        return parse_edge(text)
    except ModelError as e:
        raise ParseError(str(e))


def _cell(text: str) -> Cell:
    try:
        return Cell.parse(text)
    except ModelError as e:
        raise ParseError(str(e))


# Order matters only where patterns could overlap: "remove room" before "remove <type>".
_PATTERNS: List[tuple] = [
    (r"room %s %s (\S+)" % (_ID, _TYPE), lambda m: PlaceRoom(m[1], m[2], _cell(m[3]))),
    (r"remove room %s" % _ID, lambda m: RemoveRoom(m[1])),
    (r"wall %s" % _EDGE, lambda m: AddWall(_edge(m[1]))),
    (r"remove wall %s" % _EDGE, lambda m: RemoveWall(_edge(m[1]))),
    (r"door %s" % _EDGE, lambda m: AddDoor(_edge(m[1]))),
    (r"remove door %s" % _EDGE, lambda m: RemoveDoor(_edge(m[1]))),
    (r"window %s" % _EDGE, lambda m: AddWindow(_edge(m[1]))),
    (r"remove window %s" % _EDGE, lambda m: RemoveWindow(_edge(m[1]))),
    (r"add %s next to %s" % (_TYPE, _ID), lambda m: AddNextTo(m[1], m[2])),
    (r"remove %s %s" % (_TYPE, _ID), lambda m: RemoveTyped(m[1], m[2])),
]
_COMPILED = [(re.compile(p), build) for p, build in _PATTERNS]

_USAGE = (
    "expected one of: room <id> <type> <cell> | remove room <id> | wall <edge> | remove wall <edge> | "
    "door <edge> | remove door <edge> | window <edge> | remove window <edge> | "
    "add <type> next to <id> | remove <type> <id>"
)


def parse_command(line: str) -> Command:
    """Parse one command. Whitespace is flexible; keywords, types and ids are case-sensitive."""
    text = " ".join(line.split())
    for regex, build in _COMPILED:
        m = regex.fullmatch(text)
        if m:
            return build(m)
    raise ParseError("cannot understand %r; %s" % (text, _USAGE))


def parse_script(text: str) -> List[ScriptLine]:
    """Parse a whole script, one command per line. Blank lines are skipped.

    A line that does not parse is kept, with its error, so the caller decides what to do about it.
    """
    result: List[ScriptLine] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            result.append(ScriptLine(number, stripped, parse_command(stripped), None))
        except ParseError as e:
            result.append(ScriptLine(number, stripped, None, e.message))
    return result
