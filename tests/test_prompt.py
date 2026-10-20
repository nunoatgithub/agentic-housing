import re
import threading
from pathlib import Path

import pytest

from house.layout_format import empty_layout_text
from house.prompt import RequestError, build_prompt, check_request, fetch_layout, main
from house.server import make_server

DOC = Path("HOUSE_DSL.md")


def test_fixed_text_matches_the_document():
    template = Path("house/prompt_template.txt").read_text()
    doc_block = next(b for b in re.findall(r"```\n(.*?)```", DOC.read_text(), re.S) if b.startswith("You are an experienced"))
    # everything in the document's template except the two reference placeholders must be in ours, in order
    head, rest = doc_block.split("<command syntax reference>")
    middle, tail = rest.split("<layout format reference>")
    assert template.startswith(head)
    assert middle in template and template.rstrip().endswith(tail.rstrip())
    assert template.index(head) < template.index(middle) < template.index(tail)


def test_command_syntax_in_prompt_is_the_documents():
    syntax = next(b for b in re.findall(r"```\n(.*?)```", DOC.read_text(), re.S) if b.startswith("room R6"))
    assert syntax.rstrip() in Path("house/prompt_template.txt").read_text()


def test_slots_are_filled(example_text):
    prompt = build_prompt(example_text, "add: bathroom")
    assert "{{" not in prompt
    assert "CURRENT LAYOUT\n" + example_text + "\n\nREQUEST\nadd: bathroom\n\nReply with the script only" in prompt


def test_empty_grid_build_request():
    prompt = build_prompt(empty_layout_text(), "build: living room, kitchen, bedroom x2, bathroom")
    assert "CURRENT LAYOUT\n" + empty_layout_text() in prompt
    assert "REQUEST\nbuild: living room, kitchen, bedroom x2, bathroom\n" in prompt


def test_prompt_never_mentions_scores_or_formulas():
    text = build_prompt(empty_layout_text(), "add: bathroom").lower()
    for word in ("corridor", "privacy order", "walking distance", "compactness"):
        assert word not in text


@pytest.mark.parametrize("ok", [
    "add: bathroom", "build: living room, kitchen, bedroom x2, bathroom", "build:  kitchen",
    "remove: bedroom", "rebuild: everything",
])
def test_structured_requests_are_accepted(ok):
    assert check_request(ok)


@pytest.mark.parametrize("bad", ["", "add a bathroom please", "add bathroom", "build:", "Build: kitchen", ": kitchen"])
def test_free_text_requests_are_refused(bad):
    with pytest.raises(RequestError):
        check_request(bad)


def test_malformed_layout_is_refused():
    with pytest.raises(ValueError):
        build_prompt("grid 9x9", "add: bathroom")


def test_cli_reads_a_layout_file(capsys):
    assert main(["add: bathroom", "--layout", "examples/example_house.txt"]) == 0
    out = capsys.readouterr().out
    assert "R3  bedroom       B1" in out and out.rstrip().endswith("Reply with the script only, one command per line.")


def test_cli_empty_and_errors(capsys):
    assert main(["build: kitchen", "--empty"]) == 0
    assert "A    .    .    .    ." in capsys.readouterr().out
    assert main(["add a bathroom", "--empty"]) == 1
    assert "error: bad request" in capsys.readouterr().err
    assert main(["add: bathroom", "--server", "http://127.0.0.1:1"]) == 1


def test_cli_gets_the_current_layout_from_the_server(tmp_path, capsys, example_text):
    import io
    server = make_server(port=0, runs_dir=tmp_path, out=io.StringIO())
    threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True).start()
    url = "http://127.0.0.1:%d" % server.server_address[1]
    try:
        import urllib.request
        urllib.request.urlopen(urllib.request.Request(url + "/layout", data=example_text.encode(), method="PUT"))
        assert fetch_layout(url) == example_text
        assert main(["add: bathroom", "--server", url]) == 0
        assert "R4  bedroom       B2" in capsys.readouterr().out
    finally:
        server.shutdown()
        server.server_close()


def test_prompt_lists_the_one_kitchen_rule_and_no_merging():
    prompt = build_prompt(empty_layout_text(), "add: bathroom")
    assert "5. A house never has more than one kitchen." in prompt
    assert "merge" not in prompt.lower()


def test_the_prompt_names_the_room_types_and_has_no_hallways():
    prompt = build_prompt(empty_layout_text(), "add: bathroom")
    assert "Room types: living room, kitchen, bedroom, bathroom. There are no hallways." in prompt
    assert prompt.lower().count("hallway") == 1


def test_the_prompt_example_is_a_valid_house():
    from house.layout_format import parse_layout
    from house.rules import check_rules
    template = Path("house/prompt_template.txt").read_text()
    example = template[template.index("grid 5x5"):template.index("\n\nAn empty grid")]
    assert check_rules(parse_layout(example)) == []
    assert example == Path("examples/example_house.txt").read_text().rstrip("\n")


def test_the_prices_in_the_prompt_are_the_prices_charged():
    from house.commands import PRICES, AddDoor, AddWindow, PlaceRoom, RemoveDoor, RemoveRoom, RemoveWindow
    prompt = build_prompt(empty_layout_text(), "add: bathroom")
    listed = {}
    for line in prompt[prompt.index("COST\n"):prompt.index("\n\nLANGUAGE")].splitlines():
        m = re.fullmatch(r"(\w+), remove (\w+) +(\d+)\b.*", line)
        if m:
            listed[m[1]] = int(m[3])
    assert listed == {"room": PRICES[PlaceRoom], "door": PRICES[AddDoor], "window": PRICES[AddWindow]}
    assert PRICES[RemoveRoom] == PRICES[PlaceRoom] and PRICES[RemoveDoor] == PRICES[AddDoor] and PRICES[RemoveWindow] == PRICES[AddWindow]
    assert "Your work is also judged by the total cost of your script." in prompt


def test_the_hallway_prompt_differs_from_the_default_only_about_hallways():
    def without_example(path):
        text = Path(path).read_text()
        return text[:text.index("grid 5x5")] + text[text.index("An empty grid"):]
    plain, hallways = without_example("house/prompt_template.txt"), without_example("house/prompt_template_hallways.txt")
    for a, b in (
        ("current layout plus the ones listed. You may remove, replace or rebuild\n   rooms along the way; only the final count of each requested room type\n   matters.",
         "current layout plus the ones listed. Hallways may be added or removed\n   unless the request names them. You may remove, replace or rebuild rooms\n   along the way; only the final count of each requested room type matters."),
        ("sit further in.\n", "sit further in. Hallways are for passing through.\n"),
        ("Room types: living room, kitchen, bedroom, bathroom. There are no hallways.", "Room types: living room, kitchen, bedroom, bathroom, hallway."),
    ):
        assert plain.count(a) == 1
        plain = plain.replace(a, b)
    assert plain == hallways


def test_the_hallway_prompt_example_is_a_valid_house_with_a_hallway():
    from house.layout_format import parse_layout
    from house.rules import check_rules
    template = Path("house/prompt_template_hallways.txt").read_text()
    example = parse_layout(template[template.index("grid 5x5"):template.index("\n\nAn empty grid")])
    assert check_rules(example) == [] and "hallway" in {r.type for r in example.rooms.values()}
    assert build_prompt(empty_layout_text(), "add: bedroom", hallways=True).count("{{") == 0
