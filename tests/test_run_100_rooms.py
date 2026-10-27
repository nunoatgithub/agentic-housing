import pytest

from house.experiment import load_runs
from house.interpreter import run_script
from house.layout_format import format_layout, parse_layout
from house.model import Cell, Layout, ModelError, set_grid_size
from house.run_100_rooms import (Call, calls, label, make_call, next_call, outcome, request, rooms_added,
                                 run_next_chain, starting_house)
from house.run_agents import Reply

SEED = """room R1 living room A1
room R2 kitchen A2
room R3 bedroom B1
room R4 bathroom C1
door A1|north
door A1|A2
door A1|B1
door B1|C1"""
USAGE = {"output_tokens": 10, "cost_usd": 0.0}


@pytest.fixture
def grid15():
    set_grid_size(15)
    yield
    set_grid_size(5)


@pytest.fixture
def runs_dir(tmp_path, grid15):
    (tmp_path / "seeds").mkdir()
    (tmp_path / "seeds" / "house1.txt").write_text(format_layout(run_script(SEED, Layout()).layout) + "\n")
    return tmp_path


def record(name, valid=True):
    return {"label": name, "accepted": True, "valid": valid}


def test_a_15x15_grid_has_rows_a_to_o_and_columns_1_to_15(grid15):
    assert Cell.parse("O15") == Cell(14, 14)
    for outside in ("P1", "A16"):
        with pytest.raises(ModelError):
            Cell.parse(outside)


def test_a_room_id_may_have_any_number_of_digits(grid15):
    result = run_script("room R1000 bedroom B2\ndoor B1|B2", run_script(SEED, Layout()).layout, "add: bedroom")
    assert result.accepted and result.valid
    text = format_layout(result.layout)
    assert format_layout(parse_layout(text)) == text


def test_a_chain_alternates_one_room_steps_with_requests_for_every_room_still_missing():
    order = [str(c) for c in calls()]
    assert len(order) == 59
    assert order[:4] == ["all00", "step01", "all01", "step02"]
    assert order[-4:] == ["step28", "all28", "step29", "step30"]
    added = rooms_added(parse_layout(format_layout(run_script(SEED, Layout()).layout)))
    assert request(Call("step", 1), added) == "add: bedroom"
    assert request(Call("step", 30), added) == "add: bathroom"
    assert request(Call("all", 0), added) == "add: bedroom x15, bathroom x15"
    assert request(Call("all", 28), added) == "add: bedroom, bathroom"


def test_the_next_call_skips_valid_calls_and_failed_requests_for_all_rooms_but_stops_at_a_failed_step():
    all00, step01, all01 = (label(1, 1, c) for c in calls()[:3])
    assert next_call([], 1, 1) == (Call("all", 0), 1)
    assert next_call([record(all00, valid=False)], 1, 1) == (Call("all", 0), 2)
    assert next_call([record(all00, valid=False)] * 3, 1, 1) == (Call("step", 1), 1)
    assert next_call([record(all00), record(step01), *[record(all01, valid=False)] * 3], 1, 1) == (Call("step", 2), 1)
    assert next_call([record(all00), *[record(step01, valid=False)] * 3], 1, 1) is None


def test_a_reply_is_built_on_the_house_and_the_next_calls_start_from_the_house_it_left(runs_dir):
    reply = Reply("room R5 bedroom B2\ndoor B1|B2", USAGE)
    saved = make_call(runs_dir, 1, 1, Call("step", 1), lambda prompt: reply, "1.0")
    assert outcome(saved) == "valid"
    runs = load_runs(runs_dir)
    seed_text = (runs_dir / "seeds" / "house1.txt").read_text()
    assert starting_house(runs, seed_text, 1, 1, Call("all", 0)) == seed_text
    assert starting_house(runs, seed_text, 1, 1, Call("all", 1)) == saved["layout"]
    assert starting_house(runs, seed_text, 1, 1, Call("step", 2)) == saved["layout"]


def test_a_reply_cut_off_by_the_output_limit_is_recorded_as_cut_off_not_as_an_invalid_house(runs_dir):
    saved = make_call(runs_dir, 1, 1, Call("all", 0), lambda prompt: Reply("", USAGE, cut_off=True), "1.0")
    assert (saved["cut_off"], saved["accepted"], saved["valid"]) == (True, False, None)
    assert outcome(saved) == "reply CUT OFF"


def test_every_call_of_the_run_uses_the_same_claude_code_version(runs_dir):
    make_call(runs_dir, 1, 1, Call("all", 0), lambda prompt: Reply("", USAGE, cut_off=True), "1.0")
    with pytest.raises(SystemExit):
        run_next_chain(runs_dir, lambda prompt: Reply("", USAGE, cut_off=True), "2.0", log=lambda line: None)
