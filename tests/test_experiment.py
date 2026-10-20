import io
import threading
from pathlib import Path

import pytest

from house.experiment import (
    Label, final_house, load_runs, main, parse_label, report, request_for, send,
)
from house.layout_format import parse_layout
from house.server import make_server

A = """room R1 living room A1
room R2 kitchen A2
room R3 bedroom B1
room R4 bedroom B2
room R5 bathroom A3
door A1|north
door A1|A2
door A1|B1
door A2|B2
door A2|A3
"""
B = "room R6 bathroom B3\ndoor B2|B3\n"
C = "room R7 bedroom C1\ndoor B1|C1\n"
D = "room R8 bedroom C2\ndoor C1|C2\n"
F = B + C + D        # the big delta: all three additions in one script, on A's house
E = """room R1 living room A1
room R2 kitchen A2
room R3 bedroom B1
room R4 bedroom B2
room R5 bathroom A3
room R6 bathroom B3
room R7 bedroom C1
room R8 bedroom C2
door A1|north
door A1|A2
door A1|B1
door A2|B2
door A2|A3
door B2|B3
door B1|C1
door C1|C2
"""


@pytest.fixture(autouse=True)
def small_experiment(monkeypatch):
    """The tests run a short chain: A builds, B C D patch, E builds from scratch, F is the big delta."""
    import house.experiment as ex
    monkeypatch.setattr(ex, "STEPS", ("A", "B", "C", "D", "E", "F"))
    monkeypatch.setattr(ex, "REQUESTS", {"A": "build: living room, kitchen, bedroom x2, bathroom",
                                         "B": "add: bathroom", "C": "add: bedroom", "D": "add: bedroom"})
    monkeypatch.setattr(ex, "PATCHES", ("B", "C", "D"))
    monkeypatch.setattr(ex, "PLANNED", "E")
    monkeypatch.setattr(ex, "DELTA", "F")
    monkeypatch.setattr(ex, "PREVIOUS", {"B": "A", "C": "B", "D": "C", "F": "A"})
    monkeypatch.setattr(ex, "DRAWN", ("A", "D", "E", "F"))


@pytest.fixture
def setup(tmp_path):
    runs = tmp_path / "runs"
    server = make_server(port=0, runs_dir=runs, out=io.StringIO())
    threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True).start()
    yield runs, "http://127.0.0.1:%d" % server.server_address[1], tmp_path
    server.shutdown()
    server.server_close()


def run_chain(runs, url, chain=1, model="sonnet55", effort="medium"):
    for step, script in zip("ABCDE", (A, B, C, D, E)):
        send(Label(model, effort, chain, step), script, runs, url)


def test_labels():
    assert str(Label("sonnet55", "medium", 2, "D")) == "sonnet55-medium-c2-D"
    assert parse_label("sonnet55-medium-c2-D") == Label("sonnet55", "medium", 2, "D")
    for bad in (None, "", "claude-patch-1", "sonnet55-medium-c2", "a-b-c1-d"):
        assert parse_label(bad) is None


def test_a_whole_chain_runs_and_every_house_is_valid(setup):
    runs, url, _ = setup
    run_chain(runs, url)
    records = load_runs(runs)
    assert [r["label"] for r in records] == ["sonnet55-medium-c1-" + s for s in "ABCDE"]
    assert all(r["valid"] for r in records)
    assert [len(parse_layout(r["layout"]).rooms) for r in records] == [5, 6, 7, 8, 8]


def test_each_agent_gets_the_previous_agents_house(setup):
    runs, url, _ = setup
    run_chain(runs, url)
    records = load_runs(runs)
    records_by_step = {r["label"][-1]: r for r in records}
    for step, previous in (("B", "A"), ("C", "B"), ("D", "C")):
        layout_text, _ = request_for(step, records, Label("sonnet55", "medium", 1, step))
        assert layout_text == records_by_step[previous]["layout"]


def test_requests_for_each_step(setup):
    runs, url, _ = setup
    run_chain(runs, url)
    records = load_runs(runs)
    expected = {
        "A": "build: living room, kitchen, bedroom x2, bathroom",
        "B": "add: bathroom",
        "C": "add: bedroom",
        "D": "add: bedroom",
        "E": "build: living room, kitchen, bedroom x4, bathroom x2",
    }
    for step, request in expected.items():
        assert request_for(step, records, Label("sonnet55", "medium", 1, step))[1] == request


def test_step_needs_the_previous_step_first(setup):
    runs, url, _ = setup
    with pytest.raises(SystemExit, match="needs a valid house from step A"):
        request_for("B", load_runs(runs), Label("sonnet55", "medium", 1, "B"))


def test_send_tells_the_operator_how_it_went(setup):
    runs, url, _ = setup
    ok = send(Label("sonnet55", "medium", 1, "A"), A, runs, url)
    assert ok.endswith("valid.")
    rejected = send(Label("sonnet55", "medium", 1, "B"), "remove room R9\n", runs, url)
    assert "REJECTED" in rejected and "fresh agent" in rejected
    invalid = send(Label("sonnet55", "medium", 1, "B"), "room R6 bedroom D4\n", runs, url)
    assert "INVALID (rules 1, 2, 3, 6)" in invalid


def test_send_starts_every_step_from_the_right_house_even_after_a_failed_try(setup):
    runs, url, _ = setup
    send(Label("sonnet55", "medium", 1, "A"), A, runs, url)
    send(Label("sonnet55", "medium", 1, "B"), "room R6 bedroom D4\n", runs, url)       # invalid try
    send(Label("sonnet55", "medium", 1, "B"), B, runs, url)                             # second try
    records = load_runs(runs)
    assert len(parse_layout(records[-1]["layout"]).rooms) == 6
    assert final_house(records, Label("sonnet55", "medium", 1, "B"))["run_id"] == records[-1]["run_id"]


def test_the_model_and_effort_are_in_the_run_label(setup):
    runs, url, _ = setup
    send(Label("opus55", "high", 1, "A"), A, runs, url)
    assert load_runs(runs)[0]["label"] == "opus55-high-c1-A"



def test_report(setup):
    runs, url, _ = setup
    for chain in (1, 2, 3):
        run_chain(runs, url, chain=chain)
    send(Label("sonnet55", "medium", 1, "A"), "nonsense\n", runs, url)   # an extra failed try, does not change the final house
    text = report(load_runs(runs))
    assert "model sonnet55, effort medium, 3 chains" in text
    for n in (1, 2, 3):
        assert "chain %d" % n in text
    assert "average over chains" in text
    assert "D-E" not in text and "F-E" not in text
    lines = text.splitlines()
    chain1 = lines[lines.index(next(l for l in lines if l.startswith("chain 1  ")))+1:]
    assert next(l for l in chain1 if l.startswith("A ")).split()[1] == "2"          # two tries for A in chain 1
    assert "INVALID" not in text and "[ENTRY]" in text                                  # drawings of A, D, E


def test_report_ignores_unlabelled_runs_and_reports_missing_houses(setup):
    runs, url, _ = setup
    assert report(load_runs(runs)) == "no labelled runs found"
    send(Label("sonnet55", "medium", 1, "A"), "nonsense\n", runs, url)
    assert "no valid house" in report(load_runs(runs))


def test_command_line(setup, capsys):
    runs, url, tmp = setup
    reply = tmp / "reply.txt"
    reply.write_text(A)
    assert main(["--runs", str(runs), "send", "--chain", "1", "--step", "A", str(reply), "--server", url]) == 0
    assert "valid." in capsys.readouterr().out
    assert main(["--runs", str(runs), "prompt", "--chain", "1", "--step", "B"]) == 0
    out = capsys.readouterr().out
    assert "REQUEST\nadd: bathroom" in out and "R5  bathroom      A3" in out
    assert main(["--runs", str(runs), "report"]) == 0
    assert "chain 1" in capsys.readouterr().out


def test_runner_runs_a_chain_and_retries_a_failed_step(setup):
    from house.run_agents import run_chain
    runs, url, _ = setup
    replies = {"A": [A], "B": ["nonsense\n", B], "C": [C], "D": [D], "E": [E], "F": [F]}
    asked = []

    def fake_agent(prompt):
        # the step being asked is the first one without a valid house yet
        records = load_runs(runs)
        done = {r["label"][-1] for r in records if r["valid"]}
        step = next(s for s in "ABCDEF" if s not in done)
        asked.append(step)
        return replies[step].pop(0)

    log = []
    assert run_chain(1, "sonnet55", "medium", runs, url, 3, fake_agent, log.append) is True
    assert asked == ["A", "B", "B", "C", "D", "E", "F"]
    assert len(log) == 7 and "REJECTED" in log[1]
    assert (runs / "replies" / "sonnet55-medium-c1-B-try2.txt").read_text() == B


def test_runner_stops_a_chain_after_max_tries(setup):
    from house.run_agents import run_chain
    runs, url, _ = setup
    log = []
    assert run_chain(1, "sonnet55", "medium", runs, url, 2, lambda prompt: "nonsense", log.append) is False
    assert len(load_runs(runs)) == 2 and "chain 1 stops here" in log[-1]


def test_e_builds_every_requested_room_whatever_the_patching_agents_did(setup):
    from house.experiment import planned_request
    runs, url, _ = setup
    assert planned_request() == "build: living room, kitchen, bedroom x4, bathroom x2"
    # even with no other run at all, and even when D's house lost a bathroom
    assert request_for("E", [], Label("sonnet55", "medium", 1, "E")) == (
        parse_layout_text_empty(), "build: living room, kitchen, bedroom x4, bathroom x2")
    for step, script in zip("ABC", (A, B, C)):
        send(Label("sonnet55", "medium", 1, step), script, runs, url)
    send(Label("sonnet55", "medium", 1, "D"), "remove room R6\nroom R8 bedroom C2\ndoor C1|C2\n", runs, url)
    assert request_for("E", load_runs(runs), Label("sonnet55", "medium", 1, "E"))[1] == \
        "build: living room, kitchen, bedroom x4, bathroom x2"


def parse_layout_text_empty():
    from house.layout_format import empty_layout_text
    return empty_layout_text()


def test_runner_can_run_only_some_steps(setup):
    from house.run_agents import run_chain
    runs, url, _ = setup
    assert run_chain(1, "sonnet55", "medium", runs, url, 1, lambda prompt: E, lambda m: None, steps=["E"]) is True
    assert [r["label"] for r in load_runs(runs)] == ["sonnet55-medium-c1-E"]


def test_f_gets_a_s_house_and_is_asked_for_everything_added_later_in_one_request(setup):
    from house.experiment import delta_request
    runs, url, _ = setup
    assert delta_request() == "add: bedroom x2, bathroom"
    run_chain(runs, url)
    records = load_runs(runs)
    a = next(r for r in records if r["label"].endswith("-A"))
    layout_text, request = request_for("F", records, Label("sonnet55", "medium", 1, "F"))
    assert layout_text == a["layout"] and request == "add: bedroom x2, bathroom"


def test_f_needs_a_first(setup):
    runs, url, _ = setup
    with pytest.raises(SystemExit, match="needs a valid house from step A"):
        request_for("F", load_runs(runs), Label("sonnet55", "medium", 1, "F"))


def test_report_shows_every_step_and_draws_the_four_houses(setup):
    runs, url, _ = setup
    run_chain(runs, url)
    send(Label("sonnet55", "medium", 1, "F"), F, runs, url)
    text = report(load_runs(runs))
    assert "D-E" not in text and "F-E" not in text
    assert "chain 1: A, D, E, F" in text
    assert next(l for l in text.splitlines() if l.startswith("F ")).split()[0] == "F"


def test_claude_output_gives_text_and_token_usage():
    import json
    from house.run_agents import parse_claude_output
    stdout = json.dumps({
        "is_error": False, "result": "room R1 living room A1", "total_cost_usd": 0.0123, "duration_ms": 4000,
        "usage": {"input_tokens": 2, "cache_creation_input_tokens": 600, "cache_read_input_tokens": 100,
                  "output_tokens": 50, "output_tokens_details": {"thinking_tokens": 30}}})
    reply = parse_claude_output(stdout)
    assert reply.text == "room R1 living room A1"
    assert reply.usage == {"input_tokens": 2, "cache_creation_input_tokens": 600, "cache_read_input_tokens": 100,
                           "output_tokens": 50, "thinking_tokens": 30, "cost_usd": 0.0123, "duration_ms": 4000}
    with pytest.raises(RuntimeError):
        parse_claude_output(json.dumps({"is_error": True, "result": "Not logged in"}))


def test_usage_is_saved_in_the_run_record_and_reported(setup):
    from house.run_agents import Reply, run_chain
    runs, url, _ = setup
    usage = {"input_tokens": 2, "cache_creation_input_tokens": 600, "cache_read_input_tokens": 100,
             "output_tokens": 50, "thinking_tokens": 30, "cost_usd": 0.01, "duration_ms": 1000}
    replies = {"A": [Reply("nonsense", usage), Reply(A, usage)]}
    run_chain(1, "sonnet55", "medium", runs, url, 3, lambda prompt: replies["A"].pop(0), lambda m: None, steps=["A"])
    records = load_runs(runs)
    assert [r["agent_usage"]["output_tokens"] for r in records] == [50, 50]          # the failed try is counted too
    text = report(records)
    assert "tokens spent by the agents" in text
    a_row = next(l for l in text.splitlines() if l.startswith("A ") and "1404" in l)
    assert a_row.split() == ["A", "2", "1404", "100", "60", "0.020"]                  # calls, input, output, thinking, cost
    assert next(l for l in text.splitlines() if l.startswith("per chain")).split()[2:4] == ["2", "1404"]


def test_the_prompt_says_rooms_may_be_replaced_along_the_way():
    from house.layout_format import empty_layout_text
    from house.prompt import build_prompt
    prompt = " ".join(build_prompt(empty_layout_text(), "add: bedroom").split())
    assert "only the final count of each requested room type matters" in prompt


def test_a_run_with_hallways_gets_the_hallway_prompt_and_may_build_them(setup):
    from house.run_agents import run_chain
    runs, url, _ = setup
    with_hallway = A + "room R6 hallway C1\ndoor B1|C1\n"           # A's house with a hallway off the bedroom
    prompts = []
    def agent(prompt):
        prompts.append(prompt)
        return with_hallway
    assert run_chain(1, "sonnet55", "medium", runs, url, 1, agent, lambda m: None, steps=["A"], hallways=True)
    record = load_runs(runs)[0]
    assert record["valid"] and record["hallways"] is True and "R6  hallway" in record["layout"]
    assert "Hallways are for passing through." in prompts[0] and "There are no hallways." not in prompts[0]
