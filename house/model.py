"""Core model: grid, cells, edges, rooms, layout.

Walls are never stored: they are implied by room membership (see Layout.wall_kind).
Doors and windows are stored as sets of geometric edges.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterator, List, Optional, Set, Tuple

ROWS = 5
COLS = 5
ROW_LETTERS = "ABCDE"

ROOM_TYPES = ("living room", "kitchen", "bedroom", "bathroom")
# The houses of the 5x5 run also had hallways. The language no longer builds them (a hallway costs nothing and fixes
# any access problem, so it hid every difference between patched and planned houses), but those houses still load.
LOADABLE_TYPES = ROOM_TYPES + ("hallway",)

# Room ids are "R" followed by a number (no leading zero, at most 3 digits).
ROOM_ID_RE = re.compile(r"R[1-9][0-9]{0,2}\Z")


class ModelError(ValueError):
    """Raised when a piece of text or data does not describe a valid model object."""


class ParseError(ValueError):
    """Raised when text in the layout format or the command syntax cannot be parsed."""

    def __init__(self, message: str, line: Optional[int] = None) -> None:
        super().__init__(("line %d: %s" % (line, message)) if line is not None else message)
        self.message = message
        self.line = line


class Side(Enum):
    NORTH = "north"
    EAST = "east"
    SOUTH = "south"
    WEST = "west"


SIDE_ORDER = (Side.NORTH, Side.EAST, Side.SOUTH, Side.WEST)


@dataclass(frozen=True, order=True)
class Cell:
    """A grid square. Row 0 is "A", column 0 is "1"; ordering is row-major."""

    row: int
    col: int

    def __post_init__(self) -> None:
        if not (0 <= self.row < ROWS and 0 <= self.col < COLS):
            raise ModelError("cell (%d, %d) is outside the %dx%d grid" % (self.row, self.col, ROWS, COLS))

    def __str__(self) -> str:
        return "%s%d" % (ROW_LETTERS[self.row], self.col + 1)

    @staticmethod
    def parse(text: str) -> "Cell":
        m = re.fullmatch(r"([%s])([1-%d])" % (ROW_LETTERS, COLS), text)
        if not m:
            raise ModelError("bad cell %r: expected a letter %s-%s and a digit 1-%d, like B2" % (text, ROW_LETTERS[0], ROW_LETTERS[-1], COLS))
        return Cell(ROW_LETTERS.index(m.group(1)), int(m.group(2)) - 1)

    def neighbour(self, side: Side) -> Optional["Cell"]:
        """The adjacent cell on that side, or None if it would be outside the grid."""
        dr, dc = {Side.NORTH: (-1, 0), Side.SOUTH: (1, 0), Side.WEST: (0, -1), Side.EAST: (0, 1)}[side]
        r, c = self.row + dr, self.col + dc
        if 0 <= r < ROWS and 0 <= c < COLS:
            return Cell(r, c)
        return None

    def neighbours(self) -> List["Cell"]:
        return [n for n in (self.neighbour(s) for s in SIDE_ORDER) if n is not None]


def all_cells() -> Iterator[Cell]:
    for r in range(ROWS):
        for c in range(COLS):
            yield Cell(r, c)


@dataclass(frozen=True)
class Edge:
    """A unit segment of a grid line: the boundary between two cells, or between a cell and the outside.

    A horizontal edge (row r, col c) lies above cell (r, c), r in 0..ROWS, c in 0..COLS-1.
    A vertical edge (row r, col c) lies left of cell (r, c), r in 0..ROWS-1, c in 0..COLS.
    Every geometric edge has exactly one representation, however it was written.
    """

    horizontal: bool
    row: int
    col: int

    def __post_init__(self) -> None:
        max_row = ROWS if self.horizontal else ROWS - 1
        max_col = COLS - 1 if self.horizontal else COLS
        if not (0 <= self.row <= max_row and 0 <= self.col <= max_col):
            raise ModelError("edge outside the grid")

    @staticmethod
    def of(cell: Cell, side: Side) -> "Edge":
        if side is Side.NORTH:
            return Edge(True, cell.row, cell.col)
        if side is Side.SOUTH:
            return Edge(True, cell.row + 1, cell.col)
        if side is Side.WEST:
            return Edge(False, cell.row, cell.col)
        return Edge(False, cell.row, cell.col + 1)

    @staticmethod
    def between(a: Cell, b: Cell) -> "Edge":
        for side in SIDE_ORDER:
            if a.neighbour(side) == b:
                return Edge.of(a, side)
        raise ModelError("cells %s and %s are not neighbours" % (a, b))

    def cells(self) -> Tuple[Optional[Cell], Optional[Cell]]:
        """The two cells on either side (north/south or west/east); None means outside the grid."""
        if self.horizontal:
            before = Cell(self.row - 1, self.col) if self.row > 0 else None
            after = Cell(self.row, self.col) if self.row < ROWS else None
        else:
            before = Cell(self.row, self.col - 1) if self.col > 0 else None
            after = Cell(self.row, self.col) if self.col < COLS else None
        return before, after

    def side_of(self, cell: Cell) -> Side:
        """Which side of `cell` this edge is on."""
        for side in SIDE_ORDER:
            if Edge.of(cell, side) == self:
                return side
        raise ModelError("edge does not touch cell %s" % cell)


def all_edges() -> Iterator[Edge]:
    for r in range(ROWS + 1):
        for c in range(COLS):
            yield Edge(True, r, c)
    for r in range(ROWS):
        for c in range(COLS + 1):
            yield Edge(False, r, c)


def parse_edge(text: str) -> Edge:
    """Parse "B1|B2" (two neighbouring cells) or "A1|north" (a cell and a side)."""
    parts = text.split("|")
    if len(parts) != 2:
        raise ModelError("bad edge %r: expected two parts separated by |, like B1|B2 or A1|north" % text)
    first, second = parts
    cell = Cell.parse(first)
    sides = {s.value: s for s in Side}
    if second in sides:
        return Edge.of(cell, sides[second])
    try:
        other = Cell.parse(second)
    except ModelError:
        raise ModelError("bad edge %r: %r is neither a cell nor north/east/south/west" % (text, second))
    return Edge.between(cell, other)


@dataclass(frozen=True)
class Room:
    id: str
    type: str
    cells: frozenset  # frozenset[Cell]; the language only ever builds single-cell rooms

    def __post_init__(self) -> None:
        if not ROOM_ID_RE.match(self.id):
            raise ModelError("bad room id %r: expected R followed by a number, like R3" % self.id)
        if self.type not in LOADABLE_TYPES:
            raise ModelError("bad room type %r: expected one of %s" % (self.type, ", ".join(LOADABLE_TYPES)))
        if not self.cells:
            raise ModelError("room %s has no cells" % self.id)


def room_id_number(room_id: str) -> int:
    return int(room_id[1:])


class WallKind(Enum):
    NONE = "none"      # nothing there: same room on both sides, or no room on either side
    INNER = "inner"    # two different rooms
    OUTER = "outer"    # one room, the other side is outside (grid border or an empty cell)


@dataclass
class Layout:
    rooms: Dict[str, Room] = field(default_factory=dict)
    doors: Set[Edge] = field(default_factory=set)
    windows: Set[Edge] = field(default_factory=set)

    def copy(self) -> "Layout":
        return Layout(dict(self.rooms), set(self.doors), set(self.windows))

    def cell_map(self) -> Dict[Cell, str]:
        """Cell -> room id. If rooms overlap, the lowest id wins; structure_errors() reports it."""
        owner: Dict[Cell, str] = {}
        for room in sorted(self.rooms.values(), key=lambda r: room_id_number(r.id), reverse=True):
            for cell in room.cells:
                owner[cell] = room.id
        return owner

    def room_at(self, cell: Cell) -> Optional[Room]:
        rid = self.cell_map().get(cell)
        return self.rooms[rid] if rid else None

    def sides(self, edge: Edge) -> Tuple[Optional[str], Optional[str]]:
        """Room ids on either side of an edge (None = no room there)."""
        owner = self.cell_map()
        a, b = edge.cells()
        return (owner.get(a) if a else None, owner.get(b) if b else None)

    def wall_kind(self, edge: Edge) -> WallKind:
        a, b = self.sides(edge)
        if a == b:
            return WallKind.NONE
        if a is None or b is None:
            return WallKind.OUTER
        return WallKind.INNER

    def structure_errors(self) -> List[str]:
        """Ways this layout is not a well-formed picture (as opposed to breaking house rules)."""
        errors: List[str] = []
        claimed: Dict[Cell, str] = {}
        for room in sorted(self.rooms.values(), key=lambda r: room_id_number(r.id)):
            if self.rooms.get(room.id) is not room:
                errors.append("room %s is stored under a different id" % room.id)
            for cell in sorted(room.cells):
                if cell in claimed:
                    errors.append("cell %s belongs to both %s and %s" % (cell, claimed[cell], room.id))
                else:
                    claimed[cell] = room.id
            if not _is_contiguous(room.cells):
                errors.append("room %s is not one connected piece: %s"
                              % (room.id, " ".join(str(c) for c in sorted(room.cells))))
        for label, edges in (("door", self.doors), ("window", self.windows)):
            for edge in edges:
                if self.wall_kind(edge) is WallKind.NONE:
                    errors.append("%s on an edge with no wall: %s" % (label, edge_description(edge)))
        return errors


def edge_description(edge: Edge) -> str:
    """Layout-independent text for error messages: the edge as two sides, e.g. "A1|A2" or "A1|north"."""
    a, b = edge.cells()
    if a and b:
        return "%s|%s" % (a, b)
    cell = a or b
    assert cell is not None
    return "%s|%s" % (cell, edge.side_of(cell).value)


def _is_contiguous(cells: frozenset) -> bool:
    start = next(iter(cells))
    seen = {start}
    todo = [start]
    while todo:
        for n in todo.pop().neighbours():
            if n in cells and n not in seen:
                seen.add(n)
                todo.append(n)
    return len(seen) == len(cells)
