import pytest

from house.model import Cell, Edge, Layout, ModelError, Room, Side, WallKind, edge_description, parse_edge


def test_cell_names_round_trip():
    assert str(Cell(0, 0)) == "A1"
    assert str(Cell(3, 3)) == "D4"
    assert Cell.parse("C2") == Cell(2, 1)


@pytest.mark.parametrize("bad", ["", "F1", "A6", "A0", "a1", "A", "A11", "1A"])
def test_bad_cells_rejected(bad):
    with pytest.raises(ModelError):
        Cell.parse(bad)


def test_neighbours_and_borders():
    assert Cell(0, 0).neighbour(Side.NORTH) is None
    assert Cell(0, 0).neighbour(Side.EAST) == Cell(0, 1)
    assert [str(c) for c in Cell(1, 1).neighbours()] == ["A2", "B3", "C2", "B1"]
    assert len(Cell(0, 0).neighbours()) == 2


def test_edge_has_one_representation():
    assert parse_edge("A1|A2") == parse_edge("A2|A1") == parse_edge("A1|east") == parse_edge("A2|west")
    assert parse_edge("A1|B1") == parse_edge("B1|north") == parse_edge("A1|south")
    assert parse_edge("D4|south") == Edge(True, 4, 3)


def test_edge_cells_and_outside():
    assert parse_edge("A1|north").cells() == (None, Cell(0, 0))
    assert parse_edge("E5|east").cells() == (Cell(4, 4), None)
    assert parse_edge("B2|B3").cells() == (Cell(1, 1), Cell(1, 2))


@pytest.mark.parametrize("bad", ["A1", "A1|A3", "A1|B2", "A1|up", "A1|", "|A2", "A1|A2|A3", "Z1|north"])
def test_bad_edges_rejected(bad):
    with pytest.raises(ModelError):
        parse_edge(bad)


def test_edge_description_is_canonical():
    assert edge_description(parse_edge("A2|A1")) == "A1|A2"
    assert edge_description(parse_edge("B1|north")) == "A1|B1"
    assert edge_description(parse_edge("E4|south")) == "E4|south"


def test_room_validation():
    with pytest.raises(ModelError):
        Room("X1", "bedroom", frozenset({Cell(0, 0)}))
    with pytest.raises(ModelError):
        Room("R1", "attic", frozenset({Cell(0, 0)}))
    with pytest.raises(ModelError):
        Room("R1", "bedroom", frozenset())
    with pytest.raises(ModelError):
        Room("R01", "bedroom", frozenset({Cell(0, 0)}))


def _two_rooms() -> Layout:
    return Layout({
        "R1": Room("R1", "living room", frozenset({Cell(0, 0)})),
        "R2": Room("R2", "kitchen", frozenset({Cell(0, 1)})),
    })


def test_walls_are_implied():
    layout = _two_rooms()
    assert layout.wall_kind(parse_edge("A1|A2")) is WallKind.INNER
    assert layout.wall_kind(parse_edge("A1|north")) is WallKind.OUTER
    assert layout.wall_kind(parse_edge("A1|south")) is WallKind.OUTER   # empty cell B1 counts as outside
    assert layout.wall_kind(parse_edge("B1|B2")) is WallKind.NONE       # nothing on either side


def test_no_wall_inside_a_merged_room():
    layout = Layout({"R1": Room("R1", "living room", frozenset({Cell(0, 0), Cell(0, 1)}))})
    assert layout.wall_kind(parse_edge("A1|A2")) is WallKind.NONE
    assert layout.wall_kind(parse_edge("A2|A3")) is WallKind.OUTER


def test_structure_errors():
    overlapping = Layout({
        "R1": Room("R1", "kitchen", frozenset({Cell(0, 0)})),
        "R2": Room("R2", "bedroom", frozenset({Cell(0, 0)})),
    })
    assert any("belongs to both" in e for e in overlapping.structure_errors())

    split = Layout({"R1": Room("R1", "kitchen", frozenset({Cell(0, 0), Cell(0, 2)}))})
    assert any("not one connected piece" in e for e in split.structure_errors())

    floating_door = _two_rooms()
    floating_door.doors.add(parse_edge("C1|C2"))
    assert any("no wall" in e for e in floating_door.structure_errors())

    assert _two_rooms().structure_errors() == []


def test_copy_is_independent():
    a = _two_rooms()
    b = a.copy()
    b.doors.add(parse_edge("A1|A2"))
    assert a.doors == set()
