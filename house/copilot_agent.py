"""GitHub Copilot CLI adapter for one-shot experiment prompts."""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional

from .run_agents import Reply


def parse_copilot_output(stdout: str) -> Reply:
    """Parse Copilot CLI's JSONL event stream into the experiment's agent reply."""
    messages: List[str] = []
    deltas: List[str] = []
    usage_events: List[Dict[str, Any]] = []
    errors: List[str] = []

    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError as exc:
            raise RuntimeError("Copilot CLI returned invalid JSON on line %d: %s" % (line_number, exc)) from exc
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type", ""))
        data = event.get("data")
        if not isinstance(data, dict):
            data = {}

        if event_type == "assistant.message":
            content = data.get("content")
            if isinstance(content, str):
                messages.append(content)
        elif event_type in ("assistant.message_delta", "assistant.message.delta"):
            delta = data.get("delta", data.get("content"))
            if isinstance(delta, str):
                deltas.append(delta)
        if "usage" in event_type.lower() or "usage" in data:
            usage_events.append(event)
        if event_type in ("session.error", "assistant.error"):
            errors.append(str(data.get("message", data.get("error", event))))

    if errors:
        raise RuntimeError("Copilot CLI failed: " + "; ".join(errors)[:500])
    if messages:
        text = messages[-1]
    elif deltas:
        text = "".join(deltas)
    else:
        raise RuntimeError("Copilot CLI returned no assistant message")

    usage: Dict[str, Any] = {
        "input_tokens": None,
        "cache_creation_input_tokens": None,
        "cache_read_input_tokens": None,
        "output_tokens": None,
        "thinking_tokens": None,
        "cost_usd": None,
        "duration_ms": None,
    }
    return Reply(text, usage, metadata={"copilot_usage_events": usage_events})


def copilot_cli_version() -> str:
    return subprocess.run(["copilot", "--version"], capture_output=True, text=True, check=True).stdout.strip()


STALL_SECONDS = 60
TOTAL_SECONDS = 300


def ask_copilot(prompt: str, model_id: str, effort: str, stall_seconds: float = STALL_SECONDS,
                total_seconds: float = TOTAL_SECONDS, trace=None) -> Reply:
    """Ask Copilot CLI for one response, exposing no tools or repository context.

    The event stream is read live and traced; a call with no event for stall_seconds, or lasting longer than
    total_seconds, is killed and returned as a failed attempt instead of hanging.
    """
    trace = trace or (lambda line: print(line, file=sys.stderr, flush=True))
    lines: "queue.Queue[Optional[str]]" = queue.Queue()
    with tempfile.TemporaryDirectory() as empty_folder:
        proc = subprocess.Popen(
            ["copilot", "--prompt", prompt, "--model", model_id, "--reasoning-effort", effort,
             "--output-format", "json", "--available-tools=no_such_tool", "--allow-all-tools",
             "--disable-builtin-mcps", "--no-custom-instructions", "--no-ask-user"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=empty_folder,
            env={**os.environ, "COPILOT_DISABLE_AUTO_UPDATE": "1"},
        )

        def pump() -> None:
            for line in proc.stdout:
                lines.put(line)
            lines.put(None)

        threading.Thread(target=pump, daemon=True).start()
        start = last = time.monotonic()
        collected: List[str] = []
        failure = None
        deltas = 0
        while True:
            now = time.monotonic()
            if now - start > total_seconds:
                failure = "no reply after %ds in total" % total_seconds
            elif now - last > stall_seconds:
                failure = "no event for %ds" % stall_seconds
            if failure:
                proc.kill()
                break
            try:
                line = lines.get(timeout=1)
            except queue.Empty:
                continue
            if line is None:
                break
            last = time.monotonic()
            collected.append(line)
            try:
                event_type = json.loads(line).get("type", "?")
            except ValueError:
                event_type = "?"
            if "delta" in event_type:
                deltas += 1
                if deltas % 100 == 1:
                    trace("[copilot %4.0fs] %s x%d" % (last - start, event_type, deltas))
            else:
                trace("[copilot %4.0fs] %s" % (last - start, event_type))
        proc.wait()
    if failure:
        trace("[copilot] KILLED: " + failure)
        return Reply("", {k: None for k in ("input_tokens", "cache_creation_input_tokens",
                                            "cache_read_input_tokens", "output_tokens", "thinking_tokens",
                                            "cost_usd", "duration_ms")},
                     cut_off=True, metadata={"failure": "Copilot CLI killed: " + failure})
    if proc.returncode:
        raise RuntimeError("Copilot CLI failed: " + (proc.stderr.read() or "".join(collected)).strip()[:500])
    return parse_copilot_output("".join(collected))
