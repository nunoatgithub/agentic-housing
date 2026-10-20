import pytest

from house.interpreter import run_script
from house.layout_format import format_layout, parse_layout
from house.model import Cell, Layout

EXAMPLE_SCRIPT = """
room R1 living room A1
room R2 kitchen A2
room R3 living room B1
room R4 bedroom B2
room R5 bathroom C1
door A1|north
door A1|A2
door A1|B1
door B1|B2
door B1|C1
window A2|north
window B2|east
"""

# living room -> bedroom -> bedroom -> bathroom -> bedroom, all in a row
CHAIN_SCRIPT = """
room R1 living room A1
room R2 bedroom A2
room R3 bedroom A3
room R4 bathroom A4
room R5 bedroom B4
door A1|north
door A1|A2
door A2|A3
door A3|A4
door A4|B4
"""


def build(script, start=None):
    result = run_script(script, start)
    assert result.accepted, result.errors
    return result


def rules_broken(result):
    return sorted({v.number for v in result.violations})


# ------------------------------------------------------------ the two reference houses

def test_example_script_builds_the_example_house_and_is_valid(example_text):
    result = build(EXAMPLE_SCRIPT)
    assert result.layout == parse_layout(example_text)
    assert format_layout(result.layout) == example_text
    assert result.valid and result.violations == []
    assert result.command_count == 12


def test_chain_house_is_valid_even_though_it_is_badly_designed():
    result = build(CHAIN_SCRIPT)
    assert result.valid
    assert [r.type for r in result.layout.rooms.values()] == ["living room", "bedroom", "bedroom", "bathroom", "bedroom"]


# ------------------------------------------------------------ rule violations: built anyway, marked invalid

def test_rule1_unreachable_room():
    result = build(EXAMPLE_SCRIPT + "room R6 bedroom C2\ndoor B2|C2\nremove door B1|B2\n")
    assert rules_broken(result) == [1]
    assert [v.message.split(" cannot")[0] for v in result.violations] == ["R4 (bedroom)", "R6 (bedroom)"]
    assert len(result.layout.rooms) == 6          # still built


def test_rule1_no_entrance():
    result = build(EXAMPLE_SCRIPT + "remove door A1|north\n")
    assert 1 in rules_broken(result)
    assert any("no entrance" in v.message for v in result.violations)


def test_rule2_detached_room():
    result = build("room R1 living room A1\nroom R2 bedroom D4\ndoor A1|north\n")
    assert rules_broken(result) == [1, 2, 3]
    assert any("R2 (bedroom) shares no wall" in v.message for v in result.violations)


def test_rule3_room_without_a_door():
    result = build("room R1 living room A1\nroom R2 bedroom A2\ndoor A1|north\n")
    assert rules_broken(result) == [1, 3]


def test_rule4_outer_door_on_a_bedroom():
    result = build(CHAIN_SCRIPT + "door A2|north\n")
    assert rules_broken(result) == [4]
    assert "R2 (bedroom) has a door in an outer wall" in result.violations[0].message


def test_rule4_no_living_room():
    result = build("room R1 kitchen A1\n")
    assert rules_broken(result) == [1, 4]


def test_every_violation_is_reported():
    result = build("room R1 bedroom A1\nroom R2 kitchen D4\ndoor A1|north\n")
    assert rules_broken(result) == [1, 2, 3, 4]
    assert len(result.violations) == 7


def test_single_living_room_with_entrance_is_valid():
    assert build("room R1 living room A1\ndoor A1|north\n").valid


def test_two_entrances_in_the_living_room_are_not_forbidden():
    assert build("room R1 living room A1\ndoor A1|north\ndoor A1|west\n").valid


# ------------------------------------------------------------ rejection: any bad command rejects the script

@pytest.mark.parametrize("script,reason", [
    ("room R1 living room A1\nroom R1 kitchen A2", "already in use"),
    ("room R1 living room A1\nroom R2 kitchen A1", "already taken"),
    ("door A1|A2", "no wall"),
    ("room R1 living room A1\ndoor B1|B2", "no wall"),
    ("window A1|A2", "not an outer wall"),
    ("room R1 living room A1\nroom R2 kitchen A2\nwindow A1|A2", "not an outer wall"),
    ("remove room R9", "no room R9"),
    ("room R1 living room A1\nroom R2 kitchen A2\nremove wall A1|A2", "rooms are never joined"),
    ("add bathroom next to R3", "no room R3"),
    ("room R1 living room A1\nremove bathroom R1", "not a bathroom"),
])
def test_unworkable_command_rejects_the_whole_script(script, reason):
    result = run_script(script)
    assert not result.accepted
    assert result.layout == Layout()
    assert len(result.errors) == 1 and reason in result.errors[0].reason


def test_rejected_script_leaves_the_house_untouched_even_after_good_commands(example_text):
    start = parse_layout(example_text)
    result = run_script("room R6 bedroom D4\nremove room R99\n", start)
    assert not result.accepted
    assert result.layout == start
    assert result.errors[0].number == 2
    assert result.executed == []


def test_unparseable_line_rejects_the_script_and_all_bad_lines_are_listed():
    result = run_script("room R1 living room A1\nflurb\nwall B2|B4\n")
    assert not result.accepted
    assert [e.number for e in result.errors] == [2, 3]
    assert result.layout == Layout()
    assert result.command_count == 3


def test_run_does_not_modify_the_start_layout(example_text):
    start = parse_layout(example_text)
    run_script("remove room R5\n", start)
    assert format_layout(start) == example_text


def test_empty_script_changes_nothing(example_text):
    start = parse_layout(example_text)
    result = run_script("", start)
    assert result.accepted and result.layout == start and result.command_count == 0


# ------------------------------------------------------------ primitives and the implied-wall model

def test_remove_room_clears_cells_and_everything_on_its_walls(example_text):
    result = build("remove room R4\n", parse_layout(example_text))
    text = format_layout(result.layout)
    assert "R4" not in text
    assert "B1|B2" not in text and "B2|east" not in text
    assert "B1|C1" in text
    assert [v.number for v in result.violations] == []


def test_placing_a_room_removes_door_and_window_that_faced_the_outside():
    result = build("room R1 living room A1\ndoor A1|east\nwindow A1|south\nroom R2 kitchen A2\nroom R3 kitchen B1\n")
    assert result.layout.doors == set() and result.layout.windows == set()


def test_wall_on_an_existing_wall_does_nothing():
    base = "room R1 living room A1\nroom R2 kitchen A2\n"
    assert build(base + "wall A1|A2\nwall A1|north\n").layout == build(base).layout


def test_remove_door_and_window_that_are_not_there_do_nothing(example_text):
    start = parse_layout(example_text)
    assert build("remove door D4|north\nremove window D4|east\n", start).layout == start


# ------------------------------------------------------------ composites

def test_add_bathroom_next_to_expands_visibly_and_stays_valid(example_text):
    result = build("add bathroom next to R4\n", parse_layout(example_text))
    (executed,) = result.executed
    assert [str(c) for c in executed.expansion] == ["room R6 bathroom B3", "door B2|B3"]
    assert result.layout.rooms["R6"].type == "bathroom"
    assert result.valid


def test_new_room_gets_lowest_free_id(example_text):
    result = build("remove room R2\nadd kitchen next to R1\n", parse_layout(example_text))
    assert result.layout.rooms["R2"].type == "kitchen"      # R2 was free, so reused


def test_add_next_to_picks_first_free_cell_in_grid_order():
    result = build("room R1 living room B2\nadd bedroom next to R1\n")
    assert result.layout.rooms["R2"].cells == frozenset({Cell(0, 1)})     # A2 comes before B1, B3, C2


def test_add_next_to_with_no_free_cell_rejects():
    result = run_script("room R1 living room A1\nroom R2 kitchen A2\nroom R3 kitchen B1\nadd bedroom next to R1\n")
    assert not result.accepted and "no free cell" in result.errors[0].reason


def test_remove_typed_expands_to_remove_room(example_text):
    result = build("remove bathroom R5\n", parse_layout(example_text))
    assert [str(c) for c in result.executed[0].expansion] == ["remove room R5"]
    assert "R5" not in result.layout.rooms


def test_primitive_expansion_is_itself():
    result = build("room R1 living room A1\n")
    assert result.executed[0].expansion == (result.executed[0].command,)


def test_command_count_counts_composites_once(example_text):
    assert build("add bathroom next to R4\nadd bedroom next to R4\n", parse_layout(example_text)).command_count == 2


# ------------------------------------------------------------ rule 5: never more than one kitchen

def test_rule5_second_kitchen():
    result = build(EXAMPLE_SCRIPT + "room R6 kitchen A3\ndoor A2|A3\n")
    assert rules_broken(result) == [5]
    assert "the house has 2 kitchens (R2, R6)" in result.violations[0].message
    assert len(result.layout.rooms) == 6            # still built


def test_no_kitchen_at_all_is_allowed():
    assert build("room R1 living room A1\ndoor A1|north\n").valid


def test_merging_does_not_exist():
    result = run_script("room R1 living room A1\nroom R2 kitchen A2\nmerge R1 R2 into living room\n")
    assert not result.accepted and "cannot understand" in result.errors[0].reason


def test_a_wall_command_changes_nothing():
    base = "room R1 living room A1\nroom R2 kitchen A2\ndoor A1|A2\n"
    assert build(base + "wall A1|A2\nwall B3|B4\n").layout == build(base).layout
