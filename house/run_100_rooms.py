"""The run of paper/ANALYSIS_PLAN_100_rooms.md: four seed houses of 70 rooms grown to 100 on a 15x15 grid.

    python -m house.run_100_rooms [--runs runs_100_rooms]

Each start runs the next chain in the planned order (chain 1 on houses 1 to 4, then chain 2, then chain 3) and
stops when that chain is done. It can be stopped at any call: every call is saved as it comes back, and the next
start carries on with the call after the last one saved.

A chain starts from a seed house (runs_100_rooms/seeds/house<N>.txt) and makes these calls, in this order:
  all00, step01, all01, step02, all02, ..., step28, all28, step29, step30
stepK adds one room to the house left by step K-1 (the seed house for step01), bedroom and bathroom in turn;
allK adds every room still missing, in one request, to the house left by step K (the seed house for all00).
Every run is labelled <model>-<effort>-h<house>-c<chain>-<call>, e.g. sonnet55-medium-h1-c1-step01.

A failed call (script rejected, house invalid, reply cut off) is tried again with a fresh agent, up to 3 tries.
If a one-room step still fails, the chain stops there. Every call must use the same Claude Code version.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

from .experiment import EFFORT, MODEL, load_runs
from .interpreter import RunResult, ScriptError, run_script
from .layout_format import parse_layout
from .model import ROOM_TYPES, Layout, set_grid_size
from .prompt import build_prompt
from .recorder import build_record, next_run_id, save_record
from .run_agents import MODEL_IDS, Reply, ask_claude

# ---- the run, in one place -----------------------------------------------------------------------------------
SIZE = 15
TEMPLATE_PATH = Path(__file__).with_name("prompt_template_100_rooms.txt")
HOUSES = (1, 2, 3, 4)
CHAINS = (1, 2, 3)
STEPS = 30                                  # rooms added: 70 to 100
MAX_TRIES = 3
# ----------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Call:
    kind: str                               # "step" (one room) or "all" (every room still missing)
    step: int

    def __str__(self) -> str:
        return "%s%02d" % (self.kind, self.step)


def calls() -> List[Call]:
    """A chain's calls in the order they are made. After step 29 the one room missing is step 30's request."""
    order = [Call("all", 0)]
    for step in range(1, STEPS + 1):
        order.append(Call("step", step))
        if step < STEPS - 1:
            order.append(Call("all", step))
    return order


def label(house: int, chain: int, call: Call, model: str = MODEL, effort: str = EFFORT) -> str:
    return "%s-%s-h%d-c%d-%s" % (model, effort, house, chain, call)


def rooms_added(seed: Layout) -> List[str]:
    """The room each step adds: each time the type the house has fewer of, bedroom on a tie."""
    beds = sum(r.type == "bedroom" for r in seed.rooms.values())
    baths = sum(r.type == "bathroom" for r in seed.rooms.values())
    added = []
    for _ in range(STEPS):
        room_type = "bathroom" if baths < beds else "bedroom"
        beds, baths = beds + (room_type == "bedroom"), baths + (room_type == "bathroom")
        added.append(room_type)
    return added


def request(call: Call, added: Sequence[str]) -> str:
    if call.kind == "step":
        return "add: " + added[call.step - 1]
    missing = added[call.step:]
    counts = [(t, missing.count(t)) for t in ROOM_TYPES if missing.count(t)]
    return "add: " + ", ".join(t if n == 1 else "%s x%d" % (t, n) for t, n in counts)


def valid_house(runs: Sequence[dict], name: str) -> Optional[dict]:
    """The last valid run with this label."""
    valid = [r for r in runs if r["label"] == name and r["accepted"] and r["valid"]]
    return valid[-1] if valid else None


def next_call(runs: Sequence[dict], house: int, chain: int) -> Optional[Tuple[Call, int]]:
    """The call to make next in this chain and its try number; None once the chain is done."""
    for call in calls():
        name = label(house, chain, call)
        if valid_house(runs, name):
            continue
        tries = sum(r["label"] == name for r in runs)
        if tries < MAX_TRIES:
            return call, tries + 1
        if call.kind == "step":
            return None                     # a one-room step that still fails ends the chain
    return None


def starting_house(runs: Sequence[dict], seed_text: str, house: int, chain: int, call: Call) -> str:
    """The layout text the call starts from: the seed house, or the house a one-room step left."""
    before = call.step - 1 if call.kind == "step" else call.step
    if before == 0:
        return seed_text
    return valid_house(runs, label(house, chain, Call("step", before)))["layout"]


def make_call(runs_dir: Path, house: int, chain: int, call: Call, ask: Callable[[str], Reply], version: str) -> dict:
    """Ask a fresh agent, build its reply on the starting house and save the record."""
    runs = load_runs(runs_dir)
    seed_text = (runs_dir / "seeds" / ("house%d.txt" % house)).read_text()
    layout_text = starting_house(runs, seed_text, house, chain, call)
    wanted = request(call, rooms_added(parse_layout(seed_text)))
    reply = ask(build_prompt(layout_text, wanted, template=TEMPLATE_PATH.read_text().rstrip("\n")))
    start = parse_layout(layout_text)
    if reply.cut_off:
        result = RunResult(start, False, [ScriptError(0, "", "the reply was cut off by the output limit")])
    else:
        result = run_script(reply.text, start, wanted, hallways=True)
    run_id = next_run_id(runs_dir)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = build_record(run_id, timestamp, label(house, chain, call), reply.text, result, wanted, hallways=True)
    record.update({"cut_off": reply.cut_off, "agent_usage": reply.usage, "claude_code": version})
    save_record(runs_dir, record)
    return record


def outcome(record: dict) -> str:
    if record["cut_off"]:
        return "reply CUT OFF"
    if not record["accepted"]:
        return "script REJECTED"
    if not record["valid"]:
        return "house INVALID (rules %s)" % ", ".join(str(n) for n in sorted({v["rule"] for v in record["violations"]}))
    return "valid"


def claude_code_version() -> str:
    return subprocess.run(["claude", "--version"], capture_output=True, text=True, check=True).stdout.strip()


def run_next_chain(runs_dir: Path, ask: Callable[[str], Reply], version: str, log: Callable[[str], None] = print) -> bool:
    """Run the next chain that is not done; False if every chain is done."""
    used = {r.get("claude_code") for r in load_runs(runs_dir)} - {None, version}
    if used:
        raise SystemExit("this run's calls so far used Claude Code %s, but this is %s" % (", ".join(sorted(used)), version))
    for chain in CHAINS:
        for house in HOUSES:
            if next_call(load_runs(runs_dir), house, chain) is None:
                continue
            log("chain %d on house %d" % (chain, house))
            while (todo := next_call(load_runs(runs_dir), house, chain)) is not None:
                call, attempt = todo
                record = make_call(runs_dir, house, chain, call, ask, version)
                usage = record["agent_usage"]
                log("%s %s try %d: %s (%d output tokens, $%.3f)" % (record["run_id"], record["label"], attempt,
                                                                    outcome(record), usage["output_tokens"], usage["cost_usd"]))
            log("chain %d on house %d is done" % (chain, house))
            return True
    return False


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the next chain of the 70-to-100-room run")
    parser.add_argument("--runs", type=Path, default=Path("runs_100_rooms"))
    args = parser.parse_args(argv)
    set_grid_size(SIZE)
    ask = lambda prompt: ask_claude(prompt, MODEL_IDS[MODEL], EFFORT)
    if not run_next_chain(args.runs, ask, claude_code_version()):
        print("every chain is done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
