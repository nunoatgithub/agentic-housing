import random

import pytest

from house.layout_format import empty_layout_text, format_layout, parse_layout
from house.model import ROOM_TYPES, Cell, Edge, Layout, ModelError, ParseError, Room, WallKind, all_cells, parse_edge


def test_example_parses(example_text):
    layout = parse_layout(example_text)
    assert {rid: (r.type, sorted(map(str, r.cells))) for rid, r in layout.rooms.items()} == {
        "R1": ("living room", ["A1"]),
        "R2": ("kitchen", ["A2"]),
        "R3": ("hallway", ["B1"]),
        "R4": ("bedroom", ["B2"]),
        "R5": ("bathroom", ["C1"]),
    }
    assert layout.doors == {parse_edge(e) for e in ["A1|north", "A1|A2", "A1|B1", "B1|B2", "B1|C1"]}
    assert layout.windows == {parse_edge("A2|north"), parse_edge("B2|east")}
    assert layout.structure_errors() == []


def test_example_round_trips_exactly(example_text):
    assert format_layout(parse_layout(example_text)) == example_text


def test_example_window_faces_an_empty_cell(example_text):
    # B2|east borders the empty cell B3: it is an outer wall, written with a direction.
    layout = parse_layout(example_text)
    assert layout.wall_kind(parse_edge("B2|B3")) is WallKind.OUTER


def test_only_outer_doors_are_marked_entrance(example_text):
    lines = format_layout(parse_layout(example_text)).splitlines()
    assert [l for l in lines if "entrance" in l] == ["A1|north          entrance"]


def test_empty_grid():
    text = empty_layout_text()
    assert text.splitlines()[0:6] == [
        "grid 5x5",
        "     1    2    3    4    5",
        "A    .    .    .    .    .",
        "B    .    .    .    .    .",
        "C    .    .    .    .    .",
        "D    .    .    .    .    .",
        "E    .    .    .    .    .",
    ][0:6]
    assert text.splitlines()[6] == "E    .    .    .    .    ."
    assert text.splitlines()[7:] == ["", "rooms", "", "doors", "", "windows"]
    assert parse_layout(text) == Layout()
    assert format_layout(parse_layout(text)) == text


def test_trailing_newline_and_crlf_accepted(example_text):
    assert parse_layout(example_text + "\n\n") == parse_layout(example_text)
    assert parse_layout(example_text.replace("\n", "\r\n")) == parse_layout(example_text)


def test_non_canonical_text_is_normalised(example_text):
    shuffled = example_text.replace("A1|A2\nA1|B1", "B1|A1\nA2|A1")
    assert format_layout(parse_layout(shuffled)) == example_text


def test_merged_room_round_trip():
    text = format_layout(Layout({"R1": Room("R1", "living room", frozenset({Cell(0, 0), Cell(0, 1)}))}))
    assert "R1  living room   A1,A2" in text.splitlines()
    assert text.splitlines()[2] == "A    R1   R1   .    .    ."
    assert format_layout(parse_layout(text)) == text


def _replace(text: str, old: str, new: str) -> str:
    assert old in text
    return text.replace(old, new, 1)


@pytest.mark.parametrize("old,new,fragment", [
    ("grid 5x5", "grid 4x4", "expected 'grid 5x5'"),
    ("     1    2    3    4    5", "     1    2    3", "column numbers"),
    ("B    R3   R4   .    .    .", "B    R3   R4   .", "row label B"),
    ("B    R3   R4", "B    R3   X4", "bad grid cell"),
    ("R5  bathroom      C1", "R5  bathroom      C2", "rooms list says C2 but the grid shows C1"),
    ("R5  bathroom      C1", "R5  attic         C1", "bad room type"),
    ("R5  bathroom      C1\n", "R5  bathroom      C1\nR5  bathroom      C1\n", "listed twice"),
    ("R5  bathroom      C1\n", "", "grid uses R5"),
    ("R5  bathroom      C1\n", "R5  bathroom      C1\nR6  bedroom       D4\n", "R6"),
    ("A1|A2\n", "A1|A2\nA2|A1\n", "listed twice"),
    ("B1|C1", "C3|C4", "no wall"),
    ("B1|C1", "B1|C3", "not neighbours"),
    ("A1|A2\n", "A1|A2   entrance\n", "only for doors in an outer wall"),
    ("A2|north", "A2|north  entrance", "unexpected"),
    ("windows", "windows\nA1|A1", "not neighbours"),
    ("doors", "windows", "expected 'doors'"),
])
def test_malformed_layouts_are_rejected_with_a_reason(example_text, old, new, fragment):
    with pytest.raises(ParseError) as err:
        parse_layout(_replace(example_text, old, new))
    assert fragment in str(err.value)


def test_error_reports_line_number(example_text):
    with pytest.raises(ParseError) as err:
        parse_layout(_replace(example_text, "R5  bathroom      C1", "R5  attic         C1"))
    assert err.value.line == 14


def test_split_room_rejected():
    text = format_layout(Layout({"R1": Room("R1", "kitchen", frozenset({Cell(0, 0)}))}))
    text = text.replace("A    R1   .    .    .", "A    R1   .    R1   .").replace("kitchen       A1", "kitchen       A1,A3")
    with pytest.raises(ParseError, match="not one connected piece"):
        parse_layout(text)


def test_format_refuses_malformed_layout():
    layout = Layout({"R1": Room("R1", "kitchen", frozenset({Cell(0, 0)}))})
    layout.doors.add(parse_edge("C1|C2"))
    with pytest.raises(ModelError):
        format_layout(layout)


def _random_layout(rng: random.Random) -> Layout:
    cells = list(all_cells())
    rng.shuffle(cells)
    layout = Layout()
    n = 0
    for cell in cells[: rng.randint(0, 16)]:
        n += 1
        rid = "R%d" % (n + rng.choice([0, 20, 200]))  # varied id widths, still unique because n is
        layout.rooms[rid] = Room(rid, rng.choice(ROOM_TYPES), frozenset({cell}))
    # occasionally merge two neighbouring rooms into one
    for _ in range(rng.randint(0, 3)):
        owner = layout.cell_map()
        pairs = [(a, b) for a in owner for b in a.neighbours() if b in owner and owner[a] != owner[b]]
        if pairs:
            a, b = rng.choice(pairs)
            ra, rb = layout.rooms.pop(owner[a]), layout.rooms.pop(owner[b])
            layout.rooms[ra.id] = Room(ra.id, ra.type, ra.cells | rb.cells)
    for target in (layout.doors, layout.windows):
        for r in range(0, 5):
            for c in range(0, 5):
                for horizontal in (True, False):
                    try:
                        edge = Edge(horizontal, r, c)
                    except ModelError:
                        continue
                    if layout.wall_kind(edge) is not WallKind.NONE and rng.random() < 0.3:
                        target.add(edge)
    return layout


def test_random_layouts_round_trip():
    rng = random.Random(12345)
    for _ in range(300):
        layout = _random_layout(rng)
        assert layout.structure_errors() == []
        text = format_layout(layout)
        again = parse_layout(text)
        assert again == layout
        assert format_layout(again) == text
