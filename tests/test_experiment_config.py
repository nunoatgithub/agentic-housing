"""The real experiment configuration (the other experiment tests use a shorter chain)."""
from house import experiment as ex
from house.experiment import Label, delta_request, parse_label, planned_request, request_for
from house.layout_format import empty_layout_text


def test_the_chain():
    assert ex.STEPS == tuple("ABCDEFGHIJ")
    assert ex.REQUESTS["A"] == "build: living room, kitchen, bedroom, bathroom"      # one bedroom to start with
    assert [ex.REQUESTS[s] for s in ex.PATCHES] == ["add: bedroom", "add: bathroom"] * 3 + ["add: bedroom"]   # seven patches, types mixed
    assert ex.PREVIOUS == {"B": "A", "C": "B", "D": "C", "E": "D", "F": "E", "G": "F", "H": "G", "J": "A"}


def test_the_planned_build_asks_for_every_room_ever_requested():
    assert planned_request() == "build: living room, kitchen, bedroom x5, bathroom x4"


def test_the_big_delta_asks_for_everything_the_patches_added():
    assert delta_request() == "add: bedroom x4, bathroom x3"


def test_requests_for_the_real_steps():
    first = Label("sonnet55", "medium", 1, "A")
    assert request_for("A", [], first) == (empty_layout_text(), "build: living room, kitchen, bedroom, bathroom")
    assert request_for("I", [], Label("sonnet55", "medium", 1, "I")) == (empty_layout_text(), planned_request())


def test_all_steps_are_valid_label_letters():
    assert all(parse_label(str(Label("sonnet55", "high", 6, s))) for s in ex.STEPS)
