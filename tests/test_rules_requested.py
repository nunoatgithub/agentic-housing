from house.interpreter import run_script
from house.layout_format import parse_layout
from house.requests import parse_request
from tests.test_interpreter import EXAMPLE_SCRIPT


def rules_broken(result):
    return sorted({v.number for v in result.violations})


def test_parse_request():
    assert parse_request("build: living room, kitchen, bedroom x2, bathroom") == (
        "build", {"living room": 1, "kitchen": 1, "bedroom": 2, "bathroom": 1})
    assert parse_request("add: bedroom x2, bathroom") == ("add", {"bedroom": 2, "bathroom": 1})
    assert parse_request("add:  bedroom ×2") == ("add", {"bedroom": 2})
    for bad in (None, "", "add bedroom", "add: sauna", "remove: bedroom", "add: bedroom x"):
        assert parse_request(bad) is None


def test_build_with_exactly_the_requested_rooms_is_valid():
    result = run_script("room R1 living room A1\nroom R2 kitchen A2\nroom R3 bedroom B1\nroom R4 bedroom B2\n"
                        "room R5 bathroom C1\ndoor A1|north\ndoor A1|A2\ndoor A1|B1\ndoor B1|B2\ndoor B1|C1\n",
                        request="build: living room, kitchen, bedroom x2, bathroom")
    assert result.valid


def test_a_missing_room_makes_the_house_invalid_with_a_reason():
    result = run_script("room R1 living room A1\nroom R2 kitchen A2\ndoor A1|north\ndoor A1|A2\n",
                        request="build: living room, kitchen, bedroom, bathroom")
    assert rules_broken(result) == [6]
    assert [v.message for v in result.violations] == [
        "'build: living room, kitchen, bedroom, bathroom' needs 1 bedroom but the house has 0",
        "'build: living room, kitchen, bedroom, bathroom' needs 1 bathroom but the house has 0"]
    assert result.accepted                       # still built, and marked invalid like any rule break


def test_too_many_rooms_is_invalid_too():
    result = run_script("room R1 living room A1\nroom R2 bedroom A2\nroom R3 bedroom A3\ndoor A1|north\ndoor A1|A2\ndoor A2|A3\n",
                        request="build: living room, bedroom")
    assert rules_broken(result) == [6] and "needs 1 bedroom but the house has 2" in result.violations[0].message


def test_unlisted_types_in_a_build_are_free_and_so_are_hallways():
    result = run_script("room R1 living room A1\nroom R2 hallway A2\nroom R3 bedroom A3\nroom R4 kitchen B1\n"
                        "door A1|north\ndoor A1|A2\ndoor A2|A3\ndoor A1|B1\n", request="build: living room, bedroom")
    assert result.valid                          # the kitchen was not mentioned, the hallway never needs to be


def test_a_build_that_names_hallways_must_match_them():
    result = run_script("room R1 living room A1\nroom R2 bedroom A2\ndoor A1|north\ndoor A1|A2\n",
                        request="build: living room, bedroom, hallway")
    assert rules_broken(result) == [6]


def test_add_means_what_was_there_plus_the_additions(example_text):
    start = parse_layout(example_text)
    ok = run_script("add bedroom next to R4\n", start, "add: bedroom")
    assert ok.valid
    dropped = run_script("remove room R5\nadd bedroom next to R4\n", start, "add: bedroom")
    assert rules_broken(dropped) == [6] and "needs 1 bathroom but the house has 0" in dropped.violations[0].message
    twice = run_script("add bedroom next to R4\nadd bedroom next to R4\n", start, "add: bedroom")
    assert rules_broken(twice) == [6] and "needs 2 bedroom but the house has 3" in twice.violations[0].message


def test_demolishing_and_rebuilding_is_fine_if_the_count_comes_out_right(example_text):
    start = parse_layout(example_text)
    result = run_script("remove room R4\nroom R6 bedroom B2\ndoor B1|B2\nroom R7 bedroom B3\ndoor B2|B3\n", start, "add: bedroom")
    assert result.valid


def test_hallways_may_be_added_to_a_patch(example_text):
    start = parse_layout(example_text)
    result = run_script("room R6 hallway B3\ndoor B2|B3\nroom R7 bedroom C3\ndoor B3|C3\n", start, "add: bedroom")
    assert result.valid


def test_no_request_means_nothing_to_check():
    assert run_script(EXAMPLE_SCRIPT).valid
    assert run_script(EXAMPLE_SCRIPT, request="add a bathroom please").valid
