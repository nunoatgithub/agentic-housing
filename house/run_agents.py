"""Run the whole experiment with real agents: python -m house.run_agents [--chains 3] [--max-tries 3]

Each agent is a fresh `claude -p` call: the chosen model and effort, no tools, no memory, no settings, no MCP
servers, no saved session, and an empty working folder. It gets the prompt and nothing else, and its reply
is sent to the server exactly as written. If a step fails (script rejected or house invalid) the step is
tried again with another fresh agent, up to --max-tries; a chain stops when a step still fails.
Model and effort go in the run labels, so a later run with other settings is kept apart in the report.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence, Union

from . import experiment
from .experiment import EFFORT, MODEL, Label, attach_usage, load_runs, request_for, send
from .prompt import build_prompt

MODEL_IDS = {"sonnet55": "claude-sonnet-5-5", "opus55": "claude-opus-5-5", "fable51": "claude-fable-5-1",
             "haiku55": "claude-haiku-5-5"}
SYSTEM_PROMPT = "You are a helpful assistant."


@dataclass
class Reply:
    text: str
    usage: Dict[str, float]     # tokens and cost of this one agent call


def parse_claude_output(stdout: str) -> Reply:
    """The agent's answer and what it cost, from `claude -p --output-format json`."""
    data = json.loads(stdout)
    if data.get("is_error"):
        raise RuntimeError("claude failed: " + str(data.get("result"))[:500])
    u = data.get("usage") or {}
    return Reply(data["result"], {
        "input_tokens": u.get("input_tokens", 0),
        "cache_creation_input_tokens": u.get("cache_creation_input_tokens", 0),
        "cache_read_input_tokens": u.get("cache_read_input_tokens", 0),
        "output_tokens": u.get("output_tokens", 0),
        "thinking_tokens": (u.get("output_tokens_details") or {}).get("thinking_tokens", 0),
        "cost_usd": data.get("total_cost_usd", 0),
        "duration_ms": data.get("duration_ms", 0),
    })


def ask_claude(prompt: str, model_id: str, effort: str) -> Reply:
    with tempfile.TemporaryDirectory() as empty_folder:
        done = subprocess.run(
            ["claude", "-p", "--model", model_id, "--effort", effort, "--tools", "",
             "--no-session-persistence", "--disable-slash-commands", "--setting-sources", "",
             "--strict-mcp-config", "--system-prompt", SYSTEM_PROMPT, "--output-format", "json"],
            input=prompt, capture_output=True, text=True, timeout=900, cwd=empty_folder,
            env={**os.environ, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        )
    if done.returncode != 0:
        raise RuntimeError("claude failed: " + (done.stderr or done.stdout).strip()[:500])
    return parse_claude_output(done.stdout)


def run_chain(chain: int, model: str, effort: str, runs_dir: Path, server: str, max_tries: int,
              ask: Callable[[str], Union[str, Reply]], log: Callable[[str], None] = print, steps: Optional[Sequence[str]] = None) -> bool:
    for step in steps or experiment.STEPS:
        label = Label(model, effort, chain, step)
        for attempt in range(1, max_tries + 1):
            layout_text, request = request_for(step, load_runs(runs_dir), label)
            answer = ask(build_prompt(layout_text, request))
            reply, usage = (answer.text, answer.usage) if isinstance(answer, Reply) else (answer, None)
            replies = runs_dir / "replies"
            replies.mkdir(parents=True, exist_ok=True)
            (replies / ("%s-try%d.txt" % (label, attempt))).write_text(reply)
            outcome = send(label, reply, runs_dir, server)
            if usage:
                attach_usage(runs_dir, label, usage)
            log("%s try %d: %s" % (label, attempt, outcome))
            if outcome.endswith("valid.") and "INVALID" not in outcome:
                break
        else:
            log("%s still failing after %d tries: chain %d stops here" % (label, max_tries, chain))
            return False
    return True


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the experiment with real agents")
    parser.add_argument("--chains", type=int, default=3)
    parser.add_argument("--first-chain", type=int, default=1)
    parser.add_argument("--max-tries", type=int, default=3)
    parser.add_argument("--steps", nargs="+", choices=experiment.STEPS, default=list(experiment.STEPS), help="run only these steps")
    parser.add_argument("--model", default=MODEL, help="one of: " + ", ".join(MODEL_IDS))
    parser.add_argument("--effort", default=EFFORT)
    parser.add_argument("--runs", type=Path, default=Path("runs"))
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    args = parser.parse_args(argv)
    if args.model not in MODEL_IDS:
        parser.error("unknown model %r; known: %s" % (args.model, ", ".join(MODEL_IDS)))
    ask = lambda prompt: ask_claude(prompt, MODEL_IDS[args.model], args.effort)   # a Reply: text plus token usage
    for chain in range(args.first_chain, args.first_chain + args.chains):
        run_chain(chain, args.model, args.effort, args.runs, args.server, args.max_tries, ask, steps=args.steps)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
