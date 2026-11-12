import pytest

from house.experiment import load_runs
from house.interpreter import run_script
from house.layout_format import format_layout, parse_layout
from house.model import Cell, Layout, ModelError, set_grid_size
from house.prompt import HALLWAYS_TEMPLATE_PATH, build_prompt
from house.run_100_rooms import (COST_TEMPLATE_PATH, NO_HALLWAYS_TEMPLATE_PATH, REFACTOR_COST_TEMPLATE_PATH,
                                 REFACTOR_TEMPLATE_PATH, TEMPLATE_PATH, Call, calls, label, make_call, next_call,
                                 outcome, request, rooms_added, run_next_chain, starting_house)
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
    all00, step01, all01 = (label(1, c) for c in calls()[:3])
    assert next_call([], 1) == (Call("all", 0), 1)
    assert next_call([record(all00, valid=False)], 1) == (Call("all", 0), 2)
    assert next_call([record(all00, valid=False)] * 3, 1) == (Call("step", 1), 1)
    assert next_call([record(all00), record(step01), *[record(all01, valid=False)] * 3], 1) == (Call("step", 2), 1)
    assert next_call([record(all00), *[record(step01, valid=False)] * 3], 1) is None


def test_a_reply_is_built_on_the_house_and_the_next_calls_start_from_the_house_it_left(runs_dir):
    reply = Reply("room R5 bedroom B2\ndoor B1|B2", USAGE)
    saved = make_call(runs_dir, 1, Call("step", 1), lambda prompt: reply, "1.0")
    assert outcome(saved) == "valid"
    runs = load_runs(runs_dir)
    seed_text = (runs_dir / "seeds" / "house1.txt").read_text()
    assert starting_house(runs, seed_text, 1, Call("all", 0)) == seed_text
    assert starting_house(runs, seed_text, 1, Call("all", 1)) == saved["layout"]
    assert starting_house(runs, seed_text, 1, Call("step", 2)) == saved["layout"]


def test_call_and_chain_elapsed_times_are_saved(runs_dir):
    log = []
    assert run_next_chain(runs_dir, lambda prompt: Reply("", USAGE, cut_off=True), "1.0",
                          log=log.append, house=1)
    records = load_runs(runs_dir)
    assert records
    for saved in records:
        assert saved["call_duration_ms"] >= 0
        assert saved["chain_elapsed_ms"] >= saved["call_duration_ms"]
        assert saved["chain_started_at"] == records[0]["chain_started_at"]
        assert saved["chain_timing_estimated"] is False


def test_a_reply_cut_off_by_the_output_limit_is_recorded_as_cut_off_not_as_an_invalid_house(runs_dir):
    saved = make_call(runs_dir, 1, Call("all", 0), lambda prompt: Reply("", USAGE, cut_off=True), "1.0")
    assert (saved["cut_off"], saved["accepted"], saved["valid"]) == (True, False, None)
    assert outcome(saved) == "reply CUT OFF"


def test_every_call_of_a_chain_uses_the_same_claude_code_version(runs_dir):
    make_call(runs_dir, 1, Call("all", 0), lambda prompt: Reply("", USAGE, cut_off=True), "1.0")
    with pytest.raises(SystemExit):
        run_next_chain(runs_dir, lambda prompt: Reply("", USAGE, cut_off=True), "2.0", log=lambda line: None, house=1)


def test_a_deepseek_adapter_call_has_its_own_label_and_record(runs_dir):
    saved = make_call(runs_dir, 1, Call("step", 1), lambda prompt: Reply("room R5 bedroom B2\ndoor B1|B2", USAGE),
                      "1", chain=5, model="deepseekflash", effort="low",
                      agent_cli="deepseek-api", model_id="deepseek-flash")
    assert saved["label"] == "deepseekflash-low-h1-c5-step01"
    assert (saved["model"], saved["model_label"], saved["effort"], saved["agent_cli"]) == (
        "deepseek-flash", "deepseekflash", "low", "deepseek-api")


def test_when_no_hallway_can_be_built_a_script_that_builds_one_is_rejected_and_the_seed_houses_own_stay(runs_dir):
    seed = run_script(SEED + "\nroom R5 hallway B2\ndoor B1|B2", Layout(), hallways=True).layout
    (runs_dir / "seeds" / "house1.txt").write_text(format_layout(seed) + "\n")
    build_hallway = Reply("room R6 hallway C2\ndoor C1|C2", USAGE)
    build_bedroom = Reply("room R6 bedroom C2\ndoor C1|C2", USAGE)
    assert make_call(runs_dir, 1, Call("step", 1), lambda prompt: build_hallway, "1.0")["accepted"]
    assert not make_call(runs_dir, 1, Call("step", 1), lambda prompt: build_hallway, "1.0", hallways=False)["accepted"]
    saved = make_call(runs_dir, 1, Call("step", 1), lambda prompt: build_bedroom, "1.0", hallways=False)
    assert outcome(saved) == "valid"
    assert "R5  hallway" in saved["layout"]


def test_a_run_in_which_no_hallway_can_be_built_is_given_its_own_prompt(runs_dir):
    seed_text = (runs_dir / "seeds" / "house1.txt").read_text()
    wanted = "add: bedroom x15, bathroom x15"
    for hallways, path in ((True, TEMPLATE_PATH), (False, NO_HALLWAYS_TEMPLATE_PATH)):
        prompts = []
        make_call(runs_dir, 1, Call("all", 0), lambda prompt: prompts.append(prompt) or Reply("", USAGE), "1.0", hallways)
        assert prompts == [build_prompt(seed_text, wanted, template=path.read_text().rstrip("\n"))]


def test_a_refactor_run_asks_to_reorganise_just_before_the_request(runs_dir):
    prompts = []
    make_call(runs_dir, 1, Call("step", 1), lambda prompt: prompts.append(prompt) or Reply("", USAGE), "1.0", refactor=True)
    before, request_line = prompts[0].split("\nREQUEST\n")
    assert before.rstrip().endswith("reorganise the existing house to reduce its complexity, keeping the exact same final "
                                    "number of rooms (excluding hallways, whose number can change).")
    assert request_line.startswith("add: bedroom")
    assert prompts[0] == build_prompt((runs_dir / "seeds" / "house1.txt").read_text(), "add: bedroom",
                                      template=REFACTOR_TEMPLATE_PATH.read_text().rstrip("\n"))


def test_a_cost_run_prices_every_command_and_still_asks_to_reorganise(runs_dir):
    prompts = []
    make_call(runs_dir, 1, Call("step", 1),
              lambda prompt: prompts.append(prompt) or Reply("", USAGE), "1.0", refactor=True, cost=True)

    def cost_block(text):
        return text[text.index("COST\n"):text.index("\n\nLANGUAGE")]

    before, request_line = prompts[0].split("\nREQUEST\n")
    assert cost_block(before) == cost_block(HALLWAYS_TEMPLATE_PATH.read_text())
    assert before.rstrip().endswith("reorganise the existing house to reduce its complexity, keeping the exact same final "
                                    "number of rooms (excluding hallways, whose number can change).")
    assert request_line.startswith("add: bedroom")
    assert prompts[0] == build_prompt((runs_dir / "seeds" / "house1.txt").read_text(), "add: bedroom",
                                      template=REFACTOR_COST_TEMPLATE_PATH.read_text().rstrip("\n"))


def test_a_cost_only_run_prices_every_command_without_asking_to_reorganise(runs_dir):
    prompts = []
    make_call(runs_dir, 1, Call("step", 1),
              lambda prompt: prompts.append(prompt) or Reply("", USAGE), "1.0", cost=True)
    assert "COST\nEvery command costs something" in prompts[0]
    assert "Before you add anything" not in prompts[0]
    assert prompts[0] == build_prompt((runs_dir / "seeds" / "house1.txt").read_text(), "add: bedroom",
                                      template=COST_TEMPLATE_PATH.read_text().rstrip("\n"))


def test_the_cost_prompt_stays_on_after_a_call_that_reports_no_cost(runs_dir):
    prompts = []
    reply = Reply("", {"output_tokens": 0, "cost_usd": 0.0}, cut_off=True)
    run_next_chain(runs_dir, lambda prompt: prompts.append(prompt) or reply, "1.0",
                   log=lambda line: None, house=1, cost=True)
    assert len(prompts) == 6
    assert all("COST\nEvery command costs something" in prompt for prompt in prompts)


def test_a_house_can_be_chosen_to_run_before_the_ones_ahead_of_it(runs_dir):
    for house in (2, 3):
        (runs_dir / "seeds" / ("house%d.txt" % house)).write_text((runs_dir / "seeds" / "house1.txt").read_text())
    log = []
    assert run_next_chain(runs_dir, lambda prompt: Reply("", USAGE, cut_off=True), "1.0", log=log.append, house=3)
    assert {r["label"].split("-")[2] for r in load_runs(runs_dir)} == {"h3"}


def test_an_additional_model_chain_keeps_its_seed_and_label_separate(runs_dir):
    reply = Reply("room R5 bedroom B2\ndoor B1|B2", USAGE)
    saved = make_call(runs_dir, 1, Call("step", 1), lambda prompt: reply, "Copilot CLI 1.0",
                      hallways=False, chain=5, model="gpt6luna", effort="medium",
                      agent_cli="github-copilot-cli", seed_dir=runs_dir, model_id="gpt-6-luna")
    assert saved["label"] == "gpt6luna-medium-h1-c5-step01"
    assert saved["model"] == "gpt-6-luna"
    assert saved["model_label"] == "gpt6luna"
    assert saved["agent_cli"] == "github-copilot-cli"
    assert saved["agent_version"] == "Copilot CLI 1.0"
    assert next_call(load_runs(runs_dir), 1, chain=5, model="gpt6luna") == (Call("all", 0), 1)
