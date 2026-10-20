"""The experiment: one chain is agents A, B, C, D patching a house in turn, then E building the same rooms from scratch.

    python -m house.experiment prompt --chain 1 --step B      print the prompt for that agent
    python -m house.experiment send   --chain 1 --step B reply.txt   send the agent's reply to the server
    python -m house.experiment report                          tables and drawings for all saved runs

Every run is labelled <model>-<effort>-c<chain>-<step>, e.g. sonnet55-medium-c1-B, so the report can group them.
The layout each agent receives comes from the saved runs (the last valid house of the previous step),
so nothing depends on what the server happens to hold at that moment.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from urllib.parse import quote
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .layout_format import empty_layout_text, parse_layout
from .model import ROOM_TYPES
from .prompt import build_prompt
from .requests import parse_request
from .render import Drawing, render_side_by_side
from .scores import score

# ---- the experiment, in one place --------------------------------------------------------------------------
MODEL = "sonnet55"
EFFORT = "medium"
STEPS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")
REQUESTS = {                                # A builds the first house, B to H each patch the previous agent's house
    "A": "build: living room, kitchen, bedroom, bathroom",
    "B": "add: bedroom",                    # bedrooms and bathrooms alternate; what to demolish or rebuild is the agent's call
    "C": "add: bathroom",
    "D": "add: bedroom",
    "E": "add: bathroom",
    "F": "add: bedroom",
    "G": "add: bathroom",
    "H": "add: bedroom",
}
PATCHES = ("B", "C", "D", "E", "F", "G", "H")
PLANNED = "I"                               # builds from scratch every room that A to H were asked for
DELTA = "J"                                 # starts from A's house, asked in one go for everything B to H added
PREVIOUS = {**{s: chr(ord(s) - 1) for s in PATCHES}, DELTA: "A"}   # these start from this agent's house
DRAWN = ("A", "H", "I", "J")                # the houses drawn side by side in the report
SCORE_NAMES = ("corridor_rooms", "privacy_order", "walking_distance", "compactness")
# -------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Label:
    model: str
    effort: str
    chain: int
    step: str

    def __str__(self) -> str:
        return "%s-%s-c%d-%s" % (self.model, self.effort, self.chain, self.step)


_LABEL = re.compile(r"([^-]+)-([^-]+)-c(\d+)-([A-Z])")


def parse_label(text: Optional[str]) -> Optional[Label]:
    m = _LABEL.fullmatch(text or "")
    return Label(m[1], m[2], int(m[3]), m[4]) if m else None


def scores_of(run: dict) -> Dict[str, float]:
    """A run's scores, worked out now from its saved layout (so a change to a formula applies to old runs too)."""
    return asdict(score(parse_layout(run["layout"])))


def load_runs(runs_dir: Path) -> List[dict]:
    return [json.loads(p.read_text()) for p in sorted(runs_dir.glob("run_*.json"))]


def final_house(runs: Sequence[dict], label: Label) -> Optional[dict]:
    """The last valid run with this label: the house that gets carried to the next step."""
    valid = [r for r in runs if r["label"] == str(label) and r["accepted"] and r["valid"]]
    return valid[-1] if valid else None


def request_for(step: str, runs: Sequence[dict], label: Label) -> Tuple[str, str]:
    """(layout text, request) for a step."""
    if step in REQUESTS:
        if step in PREVIOUS:
            return _previous_layout(runs, label, PREVIOUS[step]), REQUESTS[step]
        return empty_layout_text(), REQUESTS[step]
    if step == DELTA:
        return _previous_layout(runs, label, PREVIOUS[step]), delta_request()
    return empty_layout_text(), planned_request()


def _previous_layout(runs: Sequence[dict], label: Label, previous: str) -> str:
    house = final_house(runs, Label(label.model, label.effort, label.chain, previous))
    if house is None:
        raise SystemExit("step %s needs a valid house from step %s (%s) first" % (label.step, previous, _with_step(label, previous)))
    return house["layout"]


def _with_step(label: Label, step: str) -> Label:
    return Label(label.model, label.effort, label.chain, step)


def planned_request() -> str:
    """The planned build: the rooms of the first request plus every room added after it.

    With the requests above: 'build: living room, kitchen, bedroom x4, bathroom x2'. It does not depend on
    what the patching agents actually built.
    """
    return "build: " + _room_list(_room_counts(REQUESTS.values()))


def delta_request() -> str:
    """The big delta: every room that the patch steps added one at a time, asked for in a single request."""
    additions = [REQUESTS[step] for step in PATCHES]
    return "add: " + _room_list(_room_counts(additions))


def _room_counts(requests: Iterable[str]) -> Dict[str, int]:
    counts = {t: 0 for t in ROOM_TYPES}
    for request in requests:
        for room_type, n in parse_request(request)[1].items():
            counts[room_type] += n
    return counts


def _room_list(counts: Dict[str, int]) -> str:
    return ", ".join(t if n == 1 else "%s x%d" % (t, n) for t, n in counts.items() if n)


def attach_usage(runs_dir: Path, label: Label, usage: Dict[str, float]) -> None:
    """Record what the agent call behind the latest run with this label cost, in that run's JSON file."""
    for path in sorted(runs_dir.glob("run_*.json"), reverse=True):
        record = json.loads(path.read_text())
        if record["label"] == str(label):
            record["agent_usage"] = usage
            path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
            return


# ---------------------------------------------------------------- send

def send(label: Label, script: str, runs_dir: Path, server: str) -> str:
    """Put the right starting house on the server, post the script, and say how it went (for you, not the agent)."""
    runs = load_runs(runs_dir)
    layout_text, request = request_for(label.step, runs, label)
    _http("PUT", server + "/layout", layout_text)
    _http("POST", server + "/script?label=%s&request=%s" % (label, quote(request)), script)
    mine = [r for r in load_runs(runs_dir) if r["label"] == str(label)]
    last = mine[-1]
    if not last["accepted"]:
        return "%s: script REJECTED. Run this step again with a fresh agent." % last["run_id"]
    if not last["valid"]:
        rules = sorted({v["rule"] for v in last["violations"]})
        return "%s: house INVALID (rules %s). Run this step again with a fresh agent." % (last["run_id"], ", ".join(map(str, rules)))
    return "%s: valid." % last["run_id"]


def _http(method: str, url: str, body: str) -> None:
    request = urllib.request.Request(url, data=body.encode("utf-8"), method=method)
    with urllib.request.urlopen(request, timeout=10):
        pass


# ---------------------------------------------------------------- report

Runs = Dict[Tuple[str, str], Dict[int, Dict[str, List[dict]]]]     # (model, effort) -> chain -> step -> runs


def group_runs(runs: Sequence[dict]) -> Runs:
    grouped: Runs = {}
    for run in runs:
        label = parse_label(run["label"])
        if label:
            grouped.setdefault((label.model, label.effort), {}).setdefault(label.chain, {}).setdefault(label.step, []).append(run)
    return grouped


def _fmt(value: float) -> str:
    return "%d" % value if float(value).is_integer() else "%.2f" % value


COLUMNS = ("tries", "corridor", "privacy", "walking", "compact")


def _row(name: str, cells: Sequence[str]) -> str:
    return (name.ljust(8) + "".join(c.rjust(10) for c in cells)).rstrip()


def _header(first: str) -> List[str]:
    return [_row(first, COLUMNS)]


def report(runs: Sequence[dict]) -> str:
    grouped = group_runs(runs)
    if not grouped:
        return "no labelled runs found"
    out: List[str] = []
    for (model, effort), chains in sorted(grouped.items()):
        out.append("=" * 70)
        out.append("model %s, effort %s, %d chain%s" % (model, effort, len(chains), "" if len(chains) == 1 else "s"))
        out.append("=" * 70)
        finals: Dict[int, Dict[str, dict]] = {}
        for chain, steps in sorted(chains.items()):
            out += ["", "chain %d  (tries = scripts sent for the step; the last valid one is measured)" % chain] + _header("step")
            finals[chain] = {}
            for step in STEPS:
                tries = steps.get(step, [])
                if not tries:
                    continue
                final = final_house(runs, Label(model, effort, chain, step))
                if final:
                    finals[chain][step] = final
                    s = scores_of(final)
                    out.append(_row(step, [str(len(tries))] + [_fmt(s[n]) for n in SCORE_NAMES]))
                else:
                    out.append(_row(step, [str(len(tries)), "no valid house"]))
        out += ["", "average over chains (valid houses only; n = chains measured)"]
        out.append(_row("step", ("n",) + COLUMNS[1:]) + "   tries")
        for step in STEPS:
            have = [finals[c][step] for c in finals if step in finals[c]]
            tries = [len(chains[c][step]) for c in chains if step in chains[c]]
            if have:
                means = [_mean([scores_of(h)[n] for h in have]) for n in SCORE_NAMES]
                out.append(_row(step, [str(len(have))] + [_fmt(m) for m in means]) + "   %s" % _fmt(_mean(tries)))
        out.append("(scores are all lower-is-better)")
        out += _usage_lines(runs, model, effort, len(chains))
        for chain in sorted(finals):
            drawings = [Drawing("%s (chain %d)" % (step, chain), parse_layout(finals[chain][step]["layout"]))
                        for step in DRAWN if step in finals[chain]]
            if len(drawings) >= 2:
                out += ["", "chain %d: %s" % (chain, ", ".join(d.title.split()[0] for d in drawings)), render_side_by_side(drawings)]
    return "\n".join(out)


def _usage_lines(runs: Sequence[dict], model: str, effort: str, chains: int) -> List[str]:
    """Tokens and cost of the agent calls (every try, failed ones included), by step."""
    mine = [r for r in runs if r.get("agent_usage") and parse_label(r["label"])
            and parse_label(r["label"]).model == model and parse_label(r["label"]).effort == effort]
    if not mine:
        return []
    def total(rs: Sequence[dict]) -> List[float]:
        u = [r["agent_usage"] for r in rs]
        return [len(rs),
                sum(x["input_tokens"] + x["cache_creation_input_tokens"] + x["cache_read_input_tokens"] for x in u),
                sum(x["output_tokens"] for x in u), sum(x["thinking_tokens"] for x in u), sum(x["cost_usd"] for x in u)]
    row = lambda name, v: _row(name, ["%d" % v[0], "%d" % v[1], "%d" % v[2], "%d" % v[3], "%.3f" % v[4]])
    out = ["", "tokens spent by the agents (every try, failed ones included; input = new + cached; output includes thinking)",
           _row("step", ("calls", "input", "output", "thinking", "cost $"))]
    for step in STEPS:
        rs = [r for r in mine if parse_label(r["label"]).step == step]
        if rs:
            out.append(row(step, total(rs)))
    everything = total(mine)
    out.append(row("total", everything))
    out.append(row("per chain", [v / chains for v in everything]))
    return out


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


# ---------------------------------------------------------------- command line

def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Run and measure the patch-versus-planned experiment")
    parser.add_argument("--runs", type=Path, default=Path("runs"))
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prompt", "send"):
        p = sub.add_parser(name)
        p.add_argument("--chain", type=int, required=True)
        p.add_argument("--step", choices=STEPS, required=True)
        p.add_argument("--model", default=MODEL)
        p.add_argument("--effort", default=EFFORT)
        if name == "send":
            p.add_argument("reply", type=Path, help="file holding the agent's reply, exactly as it wrote it")
            p.add_argument("--server", default="http://127.0.0.1:8000")
    sub.add_parser("report")
    args = parser.parse_args(argv)

    if args.command == "report":
        print(report(load_runs(args.runs)))
        return 0
    if "-" in args.model or "-" in args.effort:
        parser.error("model and effort must not contain '-' (it separates the parts of the label)")
    label = Label(args.model, args.effort, args.chain, args.step)
    if args.command == "prompt":
        layout_text, request = request_for(args.step, load_runs(args.runs), label)
        print(build_prompt(layout_text, request))
    else:
        print(send(label, args.reply.read_text(), args.runs, args.server))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
