import pytest

from house.commands import (
    AddDoor, AddNextTo, AddWall, AddWindow, PlaceRoom, RemoveDoor, RemoveRoom, RemoveTyped,
    RemoveWall, RemoveWindow, parse_command, parse_script,
)
from house.model import Cell, ParseError, parse_edge

DOC_SYNTAX = {
    "room R6 bedroom C2": PlaceRoom("R6", "bedroom", Cell(2, 1)),
    "remove room R6": RemoveRoom("R6"),
    "wall B2|B3": AddWall(parse_edge("B2|B3")),
    "remove wall B2|B3": RemoveWall(parse_edge("B2|B3")),
    "door B1|B2": AddDoor(parse_edge("B1|B2")),
    "door A1|north": AddDoor(parse_edge("A1|north")),
    "remove door B1|B2": RemoveDoor(parse_edge("B1|B2")),
    "window B2|east": AddWindow(parse_edge("B2|east")),
    "remove window B2|east": RemoveWindow(parse_edge("B2|east")),
    "add bathroom next to R4": AddNextTo("bathroom", "R4"),
    "remove bathroom R5": RemoveTyped("bathroom", "R5"),
}


@pytest.mark.parametrize("text,expected", DOC_SYNTAX.items())
def test_every_command_in_the_document_parses(text, expected):
    assert parse_command(text) == expected


# Without a layout a command cannot know that B2|B3 faces an empty cell, so it prints the geometric form.
GEOMETRIC_SPELLING = {"window B2|east": "window B2|B3", "remove window B2|east": "remove window B2|B3"}


@pytest.mark.parametrize("text", DOC_SYNTAX)
def test_command_prints_back_to_canonical_text(text):
    assert str(parse_command(text)) == GEOMETRIC_SPELLING.get(text, text)
    assert parse_command(str(parse_command(text))) == parse_command(text)


def test_edge_spelling_is_normalised():
    assert str(parse_command("door B2|B1")) == "door B1|B2"
    assert str(parse_command("window B3|west")) == "window B2|B3"
    assert parse_command("window B3|west") == parse_command("window B2|east")


def test_multiword_type_and_flexible_spaces():
    assert parse_command("  room   R1  living room   A1 ") == PlaceRoom("R1", "living room", Cell(0, 0))
    assert parse_command("add living room next to R2") == AddNextTo("living room", "R2")
    assert parse_command("remove living room R2") == RemoveTyped("living room", "R2")


@pytest.mark.parametrize("bad", [
    "", "build a house", "Room R1 bedroom A1", "room R1 bedroom", "room R1 attic A1", "room r1 bedroom A1",
    "room R1 bedroom F6", "room R0 bedroom A1", "room R1 bedroom A1 extra", "remove room", "remove room 6",
    "wall", "wall B2", "wall B2|B4", "door A1|up", "door A1|north now", "merge R1 R2 into living room", "add bathroom", "add bathroom next to bedroom",
    "add bathroom next to", "remove bathroom", "remove R5", "# a comment", "```",
])
def test_bad_syntax_is_a_parse_error(bad):
    with pytest.raises(ParseError):
        parse_command(bad)


def test_error_message_lists_the_syntax():
    with pytest.raises(ParseError, match="expected one of: room <id>"):
        parse_command("build a house")


def test_script_keeps_bad_lines_with_their_reason():
    lines = parse_script("room R1 living room A1\n\nflurb\r\n  door A1|north  \nwall B2|B4\n")
    assert [(l.number, l.text) for l in lines] == [
        (1, "room R1 living room A1"), (3, "flurb"), (4, "door A1|north"), (5, "wall B2|B4"),
    ]
    assert [l.command is not None for l in lines] == [True, False, True, False]
    assert all(l.error for l in lines if l.command is None)
    assert all(l.error is None for l in lines if l.command is not None)


def test_empty_script():
    assert parse_script("") == []
    assert parse_script("\n  \n") == []
