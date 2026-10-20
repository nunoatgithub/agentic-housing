"""HTTP server with the standard library.

GET  /layout   the current layout as text
POST /script   build a script on the current layout; always answers 204 with an empty body.
               The result becomes the current layout only if it is valid.
               Optional free-text label for the run: /script?label=claude-patch-1
               Optional request the script answers, so the rooms asked for can be checked:
               /script?request=add:%20bedroom
PUT  /layout   operator only: replace the current layout with the text sent; an empty body resets to an empty grid

The agent under test gets no feedback: POST /script never says whether the script was accepted, valid or
good. Everything about the run goes to the server's terminal and to the runs folder (see recorder.py).
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import IO, Callable, Optional, Sequence

from .interpreter import RunResult, run_script
from .layout_format import format_layout, parse_layout
from .model import Layout, ParseError
from .recorder import build_record, next_run_id, save_record


class App:
    """The one house being built, and where its runs are saved."""

    def __init__(self, runs_dir: Path, out: IO[str], layout: Optional[Layout] = None,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self.layout = layout or Layout()
        self.runs_dir = runs_dir
        self.out = out
        self.clock = clock

    def build(self, script: str, label: Optional[str] = None, request: Optional[str] = None) -> RunResult:
        result = run_script(script, self.layout, request)
        if result.accepted and result.valid:    # an invalid house is recorded but never built on
            self.layout = result.layout
        run_id = next_run_id(self.runs_dir) if self.runs_dir.exists() else "run_0001"
        record = build_record(run_id, self.clock().isoformat(timespec="seconds"), label, script, result, request)
        banner = ""
        if not result.accepted:
            banner = "SCRIPT REJECTED, house unchanged:\n" + "\n".join(
                "  line %d: %s -> %s" % (e.number, e.text, e.reason) for e in result.errors) + "\n\n"
        save_record(self.runs_dir, record, banner)
        self.out.write("\n" + banner + record["drawing"] + "\n")
        self.out.flush()
        return result


class Handler(BaseHTTPRequestHandler):
    server: "HouseServer"

    def do_GET(self) -> None:
        if urlsplit(self.path).path != "/layout":
            return self._reply(404)
        self._reply(200, format_layout(self.server.app.layout))

    def do_POST(self) -> None:
        url = urlsplit(self.path)
        if url.path != "/script":
            return self._reply(404)
        query = parse_qs(url.query)
        label = (query.get("label") or [None])[0] or None
        request = (query.get("request") or [None])[0] or None
        self.server.app.build(self._body(), label, request)
        self._reply(204)        # same answer whatever happened

    def do_PUT(self) -> None:
        if urlsplit(self.path).path != "/layout":
            return self._reply(404)
        text = self._body()
        try:
            layout = parse_layout(text) if text.strip() else Layout()
        except ParseError as e:
            return self._reply(400, str(e))
        self.server.app.layout = layout
        self._reply(204)

    def _body(self) -> str:
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length).decode("utf-8", errors="replace")

    def _reply(self, status: int, text: str = "") -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        if body:
            self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass                    # the terminal shows drawings, not request lines


class HouseServer(HTTPServer):
    def __init__(self, address: tuple, app: App) -> None:
        super().__init__(address, Handler)
        self.app = app


def make_server(host: str = "127.0.0.1", port: int = 8000, runs_dir: Path = Path("runs"),
                out: IO[str] = sys.stdout, layout: Optional[Layout] = None,
                clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> HouseServer:
    return HouseServer((host, port), App(runs_dir, out, layout, clock))


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="House DSL server")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--runs", type=Path, default=Path("runs"), help="folder for saved runs")
    parser.add_argument("--layout", type=Path, help="layout file to start from (default: empty grid)")
    args = parser.parse_args(argv)
    layout = parse_layout(args.layout.read_text()) if args.layout else None
    server = make_server(port=args.port, runs_dir=args.runs, layout=layout)
    print("listening on http://127.0.0.1:%d  (runs saved in %s)" % (args.port, args.runs))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
