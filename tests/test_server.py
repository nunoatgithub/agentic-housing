import io
import json
from datetime import datetime, timezone
import threading
import urllib.error
import urllib.request

import pytest

from house.layout_format import empty_layout_text
from house.server import make_server
from tests.test_interpreter import CHAIN_SCRIPT, EXAMPLE_SCRIPT


@pytest.fixture
def served(tmp_path):
    out = io.StringIO()
    server = make_server(port=0, runs_dir=tmp_path / "runs", out=out,
                         clock=lambda: datetime(2026, 10, 19, 12, 30, 5, tzinfo=timezone.utc))
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    thread.start()
    base = "http://127.0.0.1:%d" % server.server_address[1]
    yield base, out, tmp_path / "runs"
    server.shutdown()
    server.server_close()


def call(method, url, body=None):
    data = body.encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_starts_with_an_empty_grid(served):
    base, _, _ = served
    assert call("GET", base + "/layout") == (200, empty_layout_text())


def test_post_builds_and_get_returns_the_layout(served, example_text):
    base, _, _ = served
    assert call("POST", base + "/script", EXAMPLE_SCRIPT) == (204, "")
    assert call("GET", base + "/layout") == (200, example_text)


def test_post_prints_drawing_and_scores_in_the_server_terminal(served):
    base, out, _ = served
    call("POST", base + "/script", EXAMPLE_SCRIPT)
    printed = out.getvalue()
    assert "VALID" in printed and "[ENTRY]" in printed and "walking distance  1.80" in printed


def test_the_agent_gets_the_same_empty_answer_whatever_happened(served):
    base, out, _ = served
    answers = [
        call("POST", base + "/script", EXAMPLE_SCRIPT),                 # valid
        call("POST", base + "/script", "remove door A1|north"),         # builds, but invalid
        call("POST", base + "/script", "this is nonsense"),             # rejected
        call("POST", base + "/script", ""),                             # empty
    ]
    assert answers == [(204, "")] * 4
    assert "SCRIPT REJECTED" in out.getvalue()                          # visible to the operator only


def test_rejected_script_leaves_the_house_unchanged(served, example_text):
    base, _, _ = served
    call("POST", base + "/script", EXAMPLE_SCRIPT)
    call("POST", base + "/script", "remove room R1\nflurb")
    assert call("GET", base + "/layout") == (200, example_text)


def test_patching_continues_from_the_current_layout(served):
    base, _, _ = served
    call("POST", base + "/script", EXAMPLE_SCRIPT)
    call("POST", base + "/script", "room R6 bathroom B3\ndoor B2|B3")
    assert "R6  bathroom" in call("GET", base + "/layout")[1]


def test_put_loads_a_layout_and_empty_put_resets(served, example_text):
    base, _, _ = served
    assert call("PUT", base + "/layout", example_text) == (204, "")
    assert call("GET", base + "/layout") == (200, example_text)
    assert call("PUT", base + "/layout", "") == (204, "")
    assert call("GET", base + "/layout") == (200, empty_layout_text())


def test_put_rejects_a_malformed_layout_without_changing_the_house(served, example_text):
    base, _, _ = served
    call("PUT", base + "/layout", example_text)
    status, body = call("PUT", base + "/layout", "grid 9x9")
    assert status == 400 and "grid 5x5" in body
    assert call("GET", base + "/layout") == (200, example_text)


def test_unknown_paths_are_404(served):
    base, _, _ = served
    assert call("GET", base + "/scores")[0] == 404
    assert call("POST", base + "/layout", "x")[0] == 404
    assert call("GET", base + "/script")[0] == 404


def test_every_post_is_saved(served):
    base, _, runs = served
    call("POST", base + "/script", CHAIN_SCRIPT)
    call("POST", base + "/script", "flurb")
    files = sorted(p.name for p in runs.iterdir())
    assert files == ["run_0001.json", "run_0001.txt", "run_0002.json", "run_0002.txt"]
    text = (runs / "run_0001.txt").read_text()
    assert "\nSCRIPT\nroom R1 living room A1" in text and "corridor rooms    6" in text
    assert "SCRIPT REJECTED" in (runs / "run_0002.txt").read_text()


def load(runs, n):
    return json.loads((runs / ("run_%04d.json" % n)).read_text())


def test_record_has_everything(served, example_text):
    base, _, runs = served
    call("POST", base + "/script?label=initial-build", EXAMPLE_SCRIPT)
    rec = load(runs, 1)
    assert rec["run_id"] == "run_0001"
    assert rec["timestamp"] == "2026-10-19T12:30:05+00:00"
    assert rec["label"] == "initial-build"
    assert rec["command_count"] == 12
    assert rec["accepted"] is True and rec["valid"] is True
    assert rec["script"] == EXAMPLE_SCRIPT
    assert rec["layout"] == example_text
    assert "[ENTRY]" in rec["drawing"]
    assert rec["violations"] == [] and rec["errors"] == []
    assert rec["scores"] == {"corridor_rooms": 0, "privacy_order": 0.0, "walking_distance": 1.8, "compactness": 0}


def test_record_lists_violations_and_the_cost(served):
    base, _, runs = served
    call("POST", base + "/script?label=codex-patch",
         "room R1 living room A1\nroom R2 bedroom A2\ndoor A1|north\ndoor A1|A2\nroom R3 bathroom A3\ndoor A2|A3\n")
    rec = load(runs, 1)
    assert rec["command_count"] == 6
    assert rec["valid"] is True
    assert rec["cost"] == 3 * 4 + 3
    call("POST", base + "/script", "room R9 kitchen D4\n")
    rec = load(runs, 2)
    assert rec["valid"] is False and rec["scores"] is None
    assert {v["rule"] for v in rec["violations"]} == {1, 2, 3}
    assert rec["violations"][0].keys() == {"rule", "name", "message"}


def test_rejected_run_is_recorded_with_its_reasons_and_no_scores(served):
    base, _, runs = served
    call("POST", base + "/script?label=x", "room R1 living room A1\nflurb\n")
    rec = load(runs, 1)
    assert rec["accepted"] is False and rec["valid"] is None and rec["scores"] is None
    assert rec["violations"] == []
    assert rec["errors"][0]["line"] == 2 and rec["command_count"] == 2
    assert rec["layout"] == load_empty()


def load_empty():
    from house.layout_format import empty_layout_text
    return empty_layout_text()


def test_missing_label_is_null_and_run_ids_increase(served):
    base, _, runs = served
    for _ in range(3):
        call("POST", base + "/script", "")
    assert [load(runs, n)["run_id"] for n in (1, 2, 3)] == ["run_0001", "run_0002", "run_0003"]
    assert load(runs, 1)["label"] is None and load(runs, 1)["command_count"] == 0


def test_run_ids_continue_after_a_restart(tmp_path):
    from house.server import App
    runs = tmp_path / "runs"
    App(runs, io.StringIO()).build("")
    App(runs, io.StringIO()).build("")
    assert sorted(p.name for p in runs.glob("*.json")) == ["run_0001.json", "run_0002.json"]


def test_text_file_shows_labels_and_script(served):
    base, _, runs = served
    call("POST", base + "/script?label=planned-build", "room R1 living room A1\n")
    text = (runs / "run_0001.txt").read_text()
    assert text.startswith("label: planned-build   at 2026-10-19T12:30:05+00:00   commands: 1")
    assert "SCRIPT\nroom R1 living room A1" in text


def test_an_invalid_house_does_not_become_the_current_house(served, example_text):
    base, out, runs = served
    call("POST", base + "/script", EXAMPLE_SCRIPT)
    call("POST", base + "/script", "remove door A1|north")                # builds, but breaks rule 1
    assert call("GET", base + "/layout") == (200, example_text)
    assert "INVALID" in out.getvalue()
    rec = load(runs, 2)
    assert rec["valid"] is False and rec["violations"]                    # still recorded
    call("POST", base + "/script", "room R6 bathroom B3\ndoor B2|B3")     # next patch builds on the valid house
    assert "R6  bathroom" in call("GET", base + "/layout")[1]


def test_the_request_is_checked_and_recorded(served):
    base, _, runs = served
    call("POST", base + "/script?label=x&request=build:%20living%20room,%20bedroom", "room R1 living room A1\ndoor A1|north\n")
    rec = load(runs, 1)
    assert rec["request"] == "build: living room, bedroom"
    assert rec["valid"] is False and [v["rule"] for v in rec["violations"]] == [6]


def test_the_script_says_whether_hallways_are_allowed_and_the_record_keeps_it(served):
    base, _, runs = served
    script = "room R1 living room A1\nroom R2 hallway A2\ndoor A1|north\ndoor A1|A2\n"
    call("POST", base + "/script", script)
    call("POST", base + "/script?hallways=1", script)
    refused, built = load(runs, 1), load(runs, 2)
    assert refused["accepted"] is False and refused["hallways"] is False
    assert built["accepted"] is True and built["hallways"] is True and built["valid"] is True
