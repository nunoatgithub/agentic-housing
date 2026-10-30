"""The 70-to-100-room runs: four seed houses of 70 rooms grown to 100 on a 15x15 grid.

    python -m house.run_100_rooms [--runs runs_100_rooms]
    python -m house.run_100_rooms --runs runs_100_rooms_no_hallways --no-hallways [--house 3 [--chain 11]]

A run holds one or more chains per seed house; the chain number is separate from the house number and defaults to
it. Each start runs the chain of the house given, or else the next one that is
not done (houses 1 to 4 in turn), and stops when that chain is done. It can be stopped at any call: every call is saved as it comes back, and the next
start carries on with the call after the last one saved.

A chain starts from a seed house (runs_100_rooms/seeds/house<N>.txt) and makes these calls, in this order:
  all00, step01, all01, step02, all02, ..., step28, all28, step29, step30
stepK adds one room to the house left by step K-1 (the seed house for step01), bedroom and bathroom in turn;
allK adds every room still missing, in one request, to the house left by step K (the seed house for all00).
Every call is labelled <model>-<effort>-h<house>-c<chain>-<call>, e.g. sonnet55-medium-h2-c10-step01.
With --no-hallways no hallway can be built (the seed houses keep theirs, and agents may remove them); the prompt says so.

A failed call (script rejected, house invalid, reply cut off) is tried again with a fresh agent, up to 3 tries.
If a one-room step still fails, the chain stops there. Every call of a chain must use the same CLI version.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

from .experiment import EFFORT, MODEL, load_runs
from .copilot_agent import ask_copilot, copilot_cli_version
from .interpreter import RunResult, ScriptError, run_script
from .layout_format import parse_layout
from .model import ROOM_TYPES, Layout, set_grid_size
from .prompt import build_prompt
from .recorder import build_record, next_run_id, save_record
from .run_agents import MODEL_IDS, Reply, ask_claude

# ---- the run, in one place -----------------------------------------------------------------------------------
SIZE = 15
TEMPLATE_PATH = Path(__file__).with_name("prompt_template_100_rooms.txt")
NO_HALLWAYS_TEMPLATE_PATH = Path(__file__).with_name("prompt_template_100_rooms_no_hallways.txt")
HOUSES = (1, 2, 3, 4)
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


def label(house: int, call: Call, model: str = MODEL, effort: str = EFFORT,
          chain: Optional[int] = None) -> str:
    return "%s-%s-h%d-c%d-%s" % (model, effort, house, house if chain is None else chain, call)


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


def next_call(runs: Sequence[dict], house: int, chain: Optional[int] = None, model: str = MODEL,
              effort: str = EFFORT) -> Optional[Tuple[Call, int]]:
    """The call to make next in this chain and its try number; None once the chain is done."""
    for call in calls():
        name = label(house, call, model, effort, chain)
        if valid_house(runs, name):
            continue
        tries = sum(r["label"] == name for r in runs)
        if tries < MAX_TRIES:
            return call, tries + 1
        if call.kind == "step":
            return None                     # a one-room step that still fails ends the chain
    return None


def starting_house(runs: Sequence[dict], seed_text: str, house: int, call: Call, chain: Optional[int] = None,
                   model: str = MODEL, effort: str = EFFORT) -> str:
    """The layout text the call starts from: the seed house, or the house a one-room step left."""
    before = call.step - 1 if call.kind == "step" else call.step
    if before == 0:
        return seed_text
    return valid_house(runs, label(house, Call("step", before), model, effort, chain))["layout"]


def make_call(runs_dir: Path, house: int, call: Call, ask: Callable[[str], Reply], version: str,
              hallways: bool = True, chain: Optional[int] = None, model: str = MODEL, effort: str = EFFORT,
              agent_cli: str = "claude-code", seed_dir: Optional[Path] = None,
              model_id: Optional[str] = None, chain_started_at: Optional[datetime] = None,
              chain_timing_estimated: bool = False) -> dict:
    """Ask a fresh agent, build its reply on the starting house and save the record."""
    if chain_started_at is None:
        chain_started_at = datetime.now(timezone.utc)
    runs = load_runs(runs_dir)
    seed_text = ((seed_dir or runs_dir) / "seeds" / ("house%d.txt" % house)).read_text()
    layout_text = starting_house(runs, seed_text, house, call, chain, model, effort)
    wanted = request(call, rooms_added(parse_layout(seed_text)))
    template = (TEMPLATE_PATH if hallways else NO_HALLWAYS_TEMPLATE_PATH).read_text().rstrip("\n")
    call_started = time.monotonic()
    reply = ask(build_prompt(layout_text, wanted, template=template))
    call_duration_ms = round((time.monotonic() - call_started) * 1000)
    start = parse_layout(layout_text)
    if reply.cut_off:
        result = RunResult(start, False, [ScriptError(0, "", (reply.metadata or {}).get("failure", "the reply was cut off by the output limit"))])
    else:
        result = run_script(reply.text, start, wanted, hallways=hallways)
    run_id = next_run_id(runs_dir)
    completed_at = datetime.now(timezone.utc)
    timestamp = completed_at.isoformat(timespec="seconds")
    record = build_record(run_id, timestamp, label(house, call, model, effort, chain), reply.text, result, wanted,
                          hallways=hallways)
    record.update({"cut_off": reply.cut_off, "agent_usage": reply.usage, "agent_cli": agent_cli,
                   "agent_version": version, "model": model_id or model, "model_label": model, "effort": effort,
                   "call_duration_ms": call_duration_ms,
                   "chain_started_at": chain_started_at.isoformat(timespec="seconds"),
                   "chain_elapsed_ms": round((completed_at - chain_started_at).total_seconds() * 1000),
                   "chain_timing_estimated": chain_timing_estimated})
    if agent_cli == "claude-code":
        record["claude_code"] = version
    if reply.metadata:
        record["agent_metadata"] = reply.metadata
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


def run_next_chain(runs_dir: Path, ask: Callable[[str], Reply], version: str, log: Callable[[str], None] = print,
                   hallways: bool = True, house: Optional[int] = None, chain: Optional[int] = None,
                   model: str = MODEL, effort: str = EFFORT, agent_cli: str = "claude-code",
                   seed_dir: Optional[Path] = None, model_id: Optional[str] = None) -> bool:
    """Run the chain of this house, or else the next one that is not done; False if there is none."""
    for selected_house in (house,) if house else HOUSES:
        selected_chain = chain if chain is not None else selected_house
        if next_call(load_runs(runs_dir), selected_house, selected_chain, model, effort) is None:
            continue
        chain_marker = "-h%d-c%d-" % (selected_house, selected_chain)
        used = {r.get("agent_version", r.get("claude_code")) for r in load_runs(runs_dir)
                if chain_marker in r["label"]} - {None, version}
        if used:
            raise SystemExit("this chain's calls so far used %s version %s, but this is %s" %
                             (agent_cli, ", ".join(sorted(used)), version))
        existing_chain_records = [r for r in load_runs(runs_dir)
                                  if r["label"].startswith(model + "-") and chain_marker in r["label"]]
        existing_starts = [r["chain_started_at"] for r in existing_chain_records if r.get("chain_started_at")]
        chain_timing_estimated = False
        if existing_starts:
            chain_started_at = datetime.fromisoformat(min(existing_starts))
        elif existing_chain_records:
            first_record = min(existing_chain_records, key=lambda r: r["timestamp"])
            chain_started_at = datetime.fromisoformat(first_record["timestamp"])
            chain_timing_estimated = True
        else:
            chain_started_at = datetime.now(timezone.utc)
        log("house %d chain %d" % (selected_house, selected_chain))
        while (todo := next_call(load_runs(runs_dir), selected_house, selected_chain, model, effort)) is not None:
            call, attempt = todo
            record = make_call(runs_dir, selected_house, call, ask, version, hallways, selected_chain,
                               model, effort, agent_cli, seed_dir, model_id, chain_started_at,
                               chain_timing_estimated)
            usage = record["agent_usage"]
            output_tokens = usage.get("output_tokens")
            cost = usage.get("cost_usd")
            output_text = "%s output tokens" % output_tokens if output_tokens is not None else "output tokens unreported"
            cost_text = "$%.3f" % cost if cost is not None else "cost unreported"
            log("%s %s try %d: %s (%s, %s)" % (record["run_id"], record["label"], attempt,
                                               outcome(record), output_text, cost_text))
        log("house %d chain %d is done" % (selected_house, selected_chain))
        return True
    return False


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the next chain of the 70-to-100-room run")
    parser.add_argument("--runs", type=Path, help="directory for run records")
    parser.add_argument("--seed-runs", type=Path, help="directory containing the four seed layouts")
    parser.add_argument("--no-hallways", action="store_true", help="a run in which no hallway can be built")
    parser.add_argument("--house", type=int, choices=HOUSES, help="run this house's chain (default: the next one not done)")
    parser.add_argument("--chain", type=int, help="chain number (defaults to the house number)")
    parser.add_argument("--agent", choices=("claude", "copilot"), default="claude", help="CLI harness to use")
    parser.add_argument("--model", help="model ID (Copilot default: gpt-6-luna)")
    parser.add_argument("--effort", default=EFFORT, help="reasoning effort")
    args = parser.parse_args(argv)
    if args.chain is not None and args.house is None:
        parser.error("--chain requires --house")
    if args.chain is not None and args.chain < 1:
        parser.error("--chain must be positive")
    set_grid_size(SIZE)
    if args.agent == "copilot":
        model_id = args.model or "gpt-6-luna"
        model_label = re.sub(r"[^a-zA-Z0-9]+", "", model_id).lower()
        seed_source = "runs_100_rooms_no_hallways" if args.no_hallways else "runs_100_rooms"
        runs_dir = args.runs or Path(seed_source)
        seed_dir = args.seed_runs or runs_dir
        ask = lambda prompt: ask_copilot(prompt, model_id, args.effort)
        version = copilot_cli_version()
        agent_cli = "github-copilot-cli"
    else:
        model_id = args.model or MODEL_IDS[MODEL]
        model_label = MODEL if args.model is None else re.sub(r"[^a-zA-Z0-9]+", "", model_id).lower()
        runs_dir = args.runs or Path("runs_100_rooms")
        seed_dir = args.seed_runs or runs_dir
        ask = lambda prompt: ask_claude(prompt, model_id, args.effort)
        version = claude_code_version()
        agent_cli = "claude-code"
    selected_chain = args.chain if args.chain is not None else args.house
    if not run_next_chain(runs_dir, ask, version, hallways=not args.no_hallways, house=args.house,
                          chain=selected_chain, model=model_label, effort=args.effort, agent_cli=agent_cli,
                          seed_dir=seed_dir, model_id=model_id):
        print("every chain is done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
