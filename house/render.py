"""ASCII floor plans: one house, or two or three side by side.

Each cell is 7 characters wide and 3 lines tall: id, type, then a free line where vertical doorways sit.
Legend:

    |  -  +      wall
    -[   ]-      door (vertical wall: a gap)
    [ENTRY]      door in an outer wall, the entrance (vertical wall: E)
    --###--      window (vertical wall: #)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from .interpreter import RunResult
from .layout_format import parse_layout
from .model import COLS, ROW_LETTERS, ROWS, Cell, Edge, Layout, WallKind, all_edges
from .rules import Violation, check_rules
from .scores import Scores, score

CELL_W = 7
CELL_H = 3
PITCH_X = CELL_W + 1
PITCH_Y = CELL_H + 1
MARGIN = 2          # room for the row letters
GAP = "   "         # between houses in side-by-side view

SHORT_TYPE = {
    "living room": "living",
    "kitchen": "kitchen",
    "bedroom": "bedroom",
    "bathroom": "bath",
    "hallway": "hallway",
}

LEGEND = "Legend: | - + wall   -[   ]- door   [ENTRY] entrance   --###-- window"


@dataclass
class Drawing:
    title: str
    layout: Layout
    violations: Optional[List[Violation]] = None    # None: check the rules on the layout

    @staticmethod
    def of(title: str, result: RunResult) -> "Drawing":
        return Drawing(title, result.layout, result.violations)

    def broken(self) -> List[Violation]:
        return check_rules(self.layout) if self.violations is None else self.violations


def render_plan(layout: Layout) -> List[str]:
    """The grid with column numbers and row letters; every line has the same width."""
    height = ROWS * PITCH_Y + 1
    width = COLS * PITCH_X + 1
    canvas = [[" "] * width for _ in range(height)]

    for edge in all_edges():
        kind = layout.wall_kind(edge)
        if kind is WallKind.NONE:
            continue
        door, window, outer = edge in layout.doors, edge in layout.windows, kind is WallKind.OUTER
        if edge.horizontal:
            y, x = edge.row * PITCH_Y, edge.col * PITCH_X + 1
            canvas[y][x:x + CELL_W] = list(_horizontal(door, window, outer))
        else:
            x, y = edge.col * PITCH_X, edge.row * PITCH_Y + 1
            mark = "|"
            if door:
                mark = "E" if outer else " "
            elif window:
                mark = "#"
            for dy in range(CELL_H):
                canvas[y + dy][x] = mark if dy == CELL_H - 1 else "|"

    for r in range(ROWS + 1):
        for c in range(COLS + 1):
            around = []
            if c > 0:
                around.append(Edge(True, r, c - 1))
            if c < COLS:
                around.append(Edge(True, r, c))
            if r > 0:
                around.append(Edge(False, r - 1, c))
            if r < ROWS:
                around.append(Edge(False, r, c))
            if any(layout.wall_kind(e) is not WallKind.NONE for e in around):
                canvas[r * PITCH_Y][c * PITCH_X] = "+"

    for room in layout.rooms.values():
        for i, cell in enumerate(sorted(room.cells)):
            y, x = cell.row * PITCH_Y + 1, cell.col * PITCH_X + 1
            _put(canvas, y, x, room.id)
            if i == 0:
                _put(canvas, y + 1, x, SHORT_TYPE[room.type])

    header = [" "] * width
    for c in range(COLS):
        header[c * PITCH_X + 1 + CELL_W // 2] = str(c + 1)
    lines = [" " * MARGIN + "".join(header)]
    for y, row in enumerate(canvas):
        letter = ROW_LETTERS[y // PITCH_Y] if y % PITCH_Y == 2 and y // PITCH_Y < ROWS else " "
        lines.append((letter + " " * (MARGIN - 1)) + "".join(row))
    return lines


def _horizontal(door: bool, window: bool, outer: bool) -> str:
    if door:
        return "[ENTRY]" if outer else "-[   ]-"
    if window:
        return "--###--"
    return "-" * CELL_W


def _put(canvas: List[List[str]], y: int, x: int, text: str) -> None:
    text = text.center(CELL_W)
    canvas[y][x:x + CELL_W] = list(text)


def score_lines(scores: Optional[Scores]) -> List[str]:
    if scores is None:
        return ["scores: none (house is invalid)"]
    return [
        "corridor rooms    %d" % scores.corridor_rooms,
        "privacy order     %.2f" % scores.privacy_order,
        "walking distance  %.2f" % scores.walking_distance,
        "compactness       %d" % scores.compactness,
    ]


def _status(violations: List[Violation]) -> str:
    if not violations:
        return "VALID"
    numbers = sorted({v.number for v in violations})
    return "INVALID (rule%s %s)" % ("s" if len(numbers) > 1 else "", ", ".join(str(n) for n in numbers))


def _block(drawing: Drawing, details: bool) -> List[str]:
    broken = drawing.broken()
    scores = None if broken else score(drawing.layout)
    lines = [drawing.title, _status(broken), ""] + render_plan(drawing.layout) + [""] + score_lines(scores)
    if details and broken:
        lines += ["", "Broken rules:"] + ["  " + str(v) for v in broken]
    return lines


def render_house(drawing: Drawing) -> str:
    """One house: title, status, plan, scores, and the reason for every broken rule."""
    return "\n".join(line.rstrip() for line in _block(drawing, details=True) + ["", LEGEND])


def render_side_by_side(drawings: Sequence[Drawing]) -> str:
    """Two or three houses next to each other. Each is 43 characters wide (5x5 grid), so two need 89 columns."""
    width = MARGIN + COLS * PITCH_X + 1
    blocks = [[_fit(line, width) for line in _block(d, details=False)] for d in drawings]
    height = max(len(b) for b in blocks)
    rows = []
    for i in range(height):
        rows.append(GAP.join((b[i] if i < len(b) else "").ljust(width) for b in blocks).rstrip())
    return "\n".join(rows + ["", LEGEND])


def _fit(line: str, width: int) -> str:
    return line if len(line) <= width else line[: width - 3] + "..."


def main(argv: Sequence[str]) -> int:
    """python -m house.render LAYOUT_FILE [LAYOUT_FILE ...]   (2 or 3 files are drawn side by side)"""
    if not 1 <= len(argv) <= 3:
        print(main.__doc__)
        return 2
    drawings = [Drawing(Path(a).stem, parse_layout(Path(a).read_text())) for a in argv]
    print(render_house(drawings[0]) if len(drawings) == 1 else render_side_by_side(drawings))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
