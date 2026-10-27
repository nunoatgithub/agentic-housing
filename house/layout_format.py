"""Parse and print the layout text format (what GET /layout returns)."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from . import model
from .model import (
    ROOM_ID_RE,
    LOADABLE_TYPES,
    SIDE_ORDER,
    Cell,
    Edge,
    Layout,
    ModelError,
    ParseError,
    Room,
    Side,
    WallKind,
    parse_edge,
    room_id_number,
)

CELL_WIDTH = 5      # grid columns; wider only when an id needs it
ID_WIDTH = 4        # room id column in the rooms list; wider only when an id needs it
TYPE_WIDTH = 14     # room type column in the rooms list
ENTRANCE = "entrance"
EMPTY = "."


# ---------------------------------------------------------------- printing

def edge_text(layout: Layout, edge: Edge) -> str:
    """Canonical text for an edge: "A1|A2" between two rooms, "B2|east" between a room and the outside."""
    text, _ = _edge_text_and_sort_key(layout, edge)
    return text


def _edge_text_and_sort_key(layout: Layout, edge: Edge) -> Tuple[str, Tuple[Cell, int]]:
    kind = layout.wall_kind(edge)
    a, b = edge.cells()
    if kind is WallKind.INNER:
        assert a is not None and b is not None
        side = Side.SOUTH if edge.horizontal else Side.EAST
        return "%s|%s" % (a, b), (a, SIDE_ORDER.index(side))
    if kind is WallKind.OUTER:
        owner = layout.cell_map()
        room_cell = a if (a is not None and a in owner) else b
        assert room_cell is not None
        side = edge.side_of(room_cell)
        return "%s|%s" % (room_cell, side.value), (room_cell, SIDE_ORDER.index(side))
    raise ModelError("no wall on this edge, so it has no text form")


def format_layout(layout: Layout) -> str:
    """The canonical layout text, with no trailing newline."""
    errors = layout.structure_errors()
    if errors:
        raise ModelError("cannot print a malformed layout: " + "; ".join(errors))
    owner = layout.cell_map()
    lines: List[str] = [grid_header()]
    cell_width = max([CELL_WIDTH] + [len(rid) + 1 for rid in layout.rooms])
    lines.append((" " * cell_width + "".join(str(c + 1).ljust(cell_width) for c in range(model.COLS))).rstrip())
    for r in range(model.ROWS):
        row = model.ROW_LETTERS[r].ljust(cell_width)
        row += "".join(owner.get(Cell(r, c), EMPTY).ljust(cell_width) for c in range(model.COLS))
        lines.append(row.rstrip())

    lines += ["", "rooms"]
    id_width = max([ID_WIDTH] + [len(rid) + 1 for rid in layout.rooms])
    for room in sorted(layout.rooms.values(), key=lambda r: room_id_number(r.id)):
        cells = ",".join(str(c) for c in sorted(room.cells))
        lines.append(room.id.ljust(id_width) + room.type.ljust(TYPE_WIDTH) + cells)

    lines += ["", "doors"]
    for edge in _sorted_edges(layout, layout.doors):
        text = edge_text(layout, edge)
        if layout.wall_kind(edge) is WallKind.OUTER:
            lines.append(_pad(text, id_width + TYPE_WIDTH) + ENTRANCE)     # in line with the rooms' cells
        else:
            lines.append(text)

    lines += ["", "windows"]
    for edge in _sorted_edges(layout, layout.windows):
        lines.append(edge_text(layout, edge))
    return "\n".join(lines)


def grid_header() -> str:
    return "grid %dx%d" % (model.ROWS, model.COLS)


def _pad(text: str, width: int) -> str:
    """Left-justify in a column, but always leave at least one space after it."""
    return text.ljust(width) if len(text) < width else text + " "


def _sorted_edges(layout: Layout, edges: Set[Edge]) -> List[Edge]:
    """Row-major by the cell the text starts with, then north, east, south, west."""
    return sorted(edges, key=lambda e: _edge_text_and_sort_key(layout, e)[1])


# ---------------------------------------------------------------- parsing

_SECTIONS = ("rooms", "doors", "windows")


def parse_layout(text: str) -> Layout:
    """Parse layout text. Blank lines and trailing spaces are ignored; anything else must match exactly."""
    numbered = [(i + 1, line.rstrip()) for i, line in enumerate(text.splitlines())]
    numbered = [(n, line) for n, line in numbered if line.strip()]
    pos = 0

    def take(what: str) -> Tuple[int, str]:
        nonlocal pos
        if pos >= len(numbered):
            raise ParseError("unexpected end of layout, expected %s" % what)
        pos += 1
        return numbered[pos - 1]

    n, line = take("%r" % grid_header())
    if line.strip() != grid_header():
        raise ParseError("expected %r, found %r" % (grid_header(), line.strip()), n)

    n, line = take("the column numbers 1 2 3 4")
    if line.split() != [str(c + 1) for c in range(model.COLS)]:
        raise ParseError("expected the column numbers %s" % " ".join(str(c + 1) for c in range(model.COLS)), n)

    grid: Dict[Cell, str] = {}
    for r in range(model.ROWS):
        n, line = take("row %s of the grid" % model.ROW_LETTERS[r])
        tokens = line.split()
        if len(tokens) != model.COLS + 1 or tokens[0] != model.ROW_LETTERS[r]:
            raise ParseError("expected row label %s followed by %d cells" % (model.ROW_LETTERS[r], model.COLS), n)
        for c, token in enumerate(tokens[1:]):
            if token == EMPTY:
                continue
            if not ROOM_ID_RE.match(token):
                raise ParseError("bad grid cell %r: expected a room id like R3 or '.'" % token, n)
            grid[Cell(r, c)] = token

    sections: Dict[str, List[Tuple[int, str]]] = {}
    for name in _SECTIONS:
        n, line = take("the %r section" % name)
        if line.strip() != name:
            raise ParseError("expected %r, found %r" % (name, line.strip()), n)
        entries: List[Tuple[int, str]] = []
        while pos < len(numbered) and numbered[pos][1].strip() not in _SECTIONS:
            entries.append(numbered[pos])
            pos += 1
        sections[name] = entries
    if pos < len(numbered):
        n, line = numbered[pos]
        raise ParseError("unexpected %r" % line.strip(), n)

    layout = Layout()
    room_lines: Dict[str, int] = {}
    for n, line in sections["rooms"]:
        room = _parse_room_line(line, n)
        if room.id in layout.rooms:
            raise ParseError("room %s is listed twice" % room.id, n)
        layout.rooms[room.id] = room
        room_lines[room.id] = n

    for rid in sorted({*grid.values(), *layout.rooms}, key=room_id_number):
        in_grid = frozenset(c for c, owner in grid.items() if owner == rid)
        if rid not in layout.rooms:
            raise ParseError("the grid uses %s but the rooms list does not have it" % rid)
        if layout.rooms[rid].cells != in_grid:
            raise ParseError(
                "room %s: the rooms list says %s but the grid shows %s"
                % (rid, _cells_text(layout.rooms[rid].cells), _cells_text(in_grid) or "no cells"),
                room_lines[rid],
            )

    structure = layout.structure_errors()  # doors and windows are not added yet: only room shapes so far
    if structure:
        raise ParseError(structure[0])

    for name, target in (("doors", layout.doors), ("windows", layout.windows)):
        for n, line in sections[name]:
            edge, annotation = _parse_edge_line(line, n, allow_entrance=(name == "doors"))
            if edge in target:
                raise ParseError("%s %s is listed twice" % (name[:-1], line.split()[0]), n)
            kind = layout.wall_kind(edge)
            if kind is WallKind.NONE:
                raise ParseError("%s on %s: there is no wall there" % (name[:-1], line.split()[0]), n)
            if annotation and kind is not WallKind.OUTER:
                raise ParseError("%r is only for doors in an outer wall" % ENTRANCE, n)
            target.add(edge)
    return layout


def _cells_text(cells: frozenset) -> str:
    return ",".join(str(c) for c in sorted(cells))


def _parse_room_line(line: str, n: int) -> Room:
    tokens = line.split()
    if len(tokens) < 3:
        raise ParseError("expected '<id> <type> <cells>', like 'R1  living room   A1'", n)
    room_id, type_words, cell_token = tokens[0], " ".join(tokens[1:-1]), tokens[-1]
    if not ROOM_ID_RE.match(room_id):
        raise ParseError("bad room id %r: expected R followed by a number, like R3" % room_id, n)
    if type_words not in LOADABLE_TYPES:
        raise ParseError("bad room type %r: expected one of %s" % (type_words, ", ".join(LOADABLE_TYPES)), n)
    try:
        cells = [Cell.parse(t) for t in cell_token.split(",")]
    except ModelError as e:
        raise ParseError(str(e), n)
    if len(set(cells)) != len(cells):
        raise ParseError("room %s lists a cell twice" % room_id, n)
    return Room(room_id, type_words, frozenset(cells))


def _parse_edge_line(line: str, n: int, allow_entrance: bool) -> Tuple[Edge, Optional[str]]:
    tokens = line.split()
    if len(tokens) > 2 or (len(tokens) == 2 and not (allow_entrance and tokens[1] == ENTRANCE)):
        extra = " ".join(tokens[1:])
        raise ParseError("unexpected %r after the edge%s" % (extra, " (only 'entrance' is allowed)" if allow_entrance else ""), n)
    try:
        edge = parse_edge(tokens[0])
    except ModelError as e:
        raise ParseError(str(e), n)
    return edge, (tokens[1] if len(tokens) == 2 else None)


def empty_layout_text() -> str:
    return format_layout(Layout())
