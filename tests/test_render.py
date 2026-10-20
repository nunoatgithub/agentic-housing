from pathlib import Path

from house.interpreter import run_script
from house.layout_format import parse_layout
from house.render import Drawing, render_house, render_plan, render_side_by_side
from tests.test_interpreter import CHAIN_SCRIPT, EXAMPLE_SCRIPT

EXAMPLE_PLAN = [
    "      1       2       3       4       5",
    "  +[ENTRY]+--###--+",
    "  |   R1  |   R2  |",
    "A | living|kitchen|",
    "  |               |",
    "  +-[   ]-+-------+",
    "  |   R3  |   R4  |",
    "B | living|bedroom|",
    "  |               #",
    "  +-[   ]-+-------+",
    "  |   R5  |",
    "C |  bath |",
    "  |       |",
    "  +-------+",
    "",
    "D",
    "",
    "",
    "",
    "E",
    "",
    "",
]


def example():
    return run_script(EXAMPLE_SCRIPT).layout


def test_example_plan_exact():
    assert [l.rstrip() for l in render_plan(example())] == EXAMPLE_PLAN


def test_every_plan_line_has_the_same_width():
    assert len({len(l) for l in render_plan(example())}) == 1


def test_entrance_is_marked_once_in_the_example():
    assert render_house(Drawing("x", example())).count("[ENTRY]") == 2    # once in the plan, once in the legend


def test_door_window_and_walls_are_distinguishable():
    plan = "\n".join(render_plan(example()))
    assert "-[   ]-" in plan and "--###--" in plan and "[ENTRY]" in plan
    assert "#" in plan.splitlines()[8]          # vertical window B2|east


def test_single_house_shows_scores_and_status():
    text = render_house(Drawing("example", example()))
    assert text.splitlines()[:2] == ["example", "VALID"]
    for line in ("corridor rooms    0", "privacy order     0.00", "walking distance  1.80", "compactness       0"):
        assert line in text


def test_invalid_house_lists_every_broken_rule_and_no_scores():
    result = run_script("room R1 bedroom A1\nroom R2 kitchen D4\ndoor A1|north\n")
    text = render_house(Drawing.of("bad", result))
    assert "INVALID (rules 1, 2, 3, 4)" in text
    assert "scores: none" in text and "corridor rooms" not in text
    assert text.count("\n  rule ") == 7


def test_side_by_side_aligns_and_fits_89_columns_for_two():
    a, b = Drawing("example", example()), Drawing("chain", run_script(CHAIN_SCRIPT).layout)
    text = render_side_by_side([a, b])
    assert max(len(l) for l in text.splitlines()) <= 89
    lines = text.splitlines()
    assert lines[0].split() == ["example", "chain"]
    row = next(l for l in lines if l.startswith("corridor"))
    assert row.startswith("corridor rooms    0") and row.count("corridor rooms") == 2 and row.rstrip().endswith("6")


def test_three_side_by_side():
    ds = [Drawing(n, parse_layout(Path("examples/%s.txt" % n).read_text()))
          for n in ("example_house", "chain_house", "broken_house")]
    text = render_side_by_side(ds)
    assert max(len(l) for l in text.splitlines()) <= 135
    assert "INVALID" in text and text.splitlines()[0].split() == ["example_house", "chain_house", "broken_house"]


def test_output_is_plain_ascii():
    text = render_house(Drawing("example", example())) + render_side_by_side([Drawing("a", example())] * 3)
    assert text.isascii()


def test_rendering_is_deterministic():
    assert render_house(Drawing("x", example())) == render_house(Drawing("x", example()))
