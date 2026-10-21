"""Fill the standard prompt template with the current layout and a request, ready to paste into a fresh agent.

    python -m house.prompt "add: bathroom"                       layout from the running server
    python -m house.prompt "add: bathroom" --layout house.txt    layout from a file
    python -m house.prompt "build: living room, kitchen, bedroom x2, bathroom" --empty

The template is house/prompt_template.txt.
For a run that allows hallways (--hallways) it is house/prompt_template_hallways.txt.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Sequence

from .layout_format import empty_layout_text, format_layout, parse_layout

TEMPLATE_PATH = Path(__file__).with_name("prompt_template.txt")
HALLWAYS_TEMPLATE_PATH = Path(__file__).with_name("prompt_template_hallways.txt")

_REQUEST = re.compile(r"[a-z][a-z-]*: \S.*")


class RequestError(ValueError):
    pass


def check_request(request: str) -> str:
    """Requests are structured, never a free-form sentence: '<keyword>: <details>', like 'add: bathroom'."""
    request = " ".join(request.split())
    if not _REQUEST.fullmatch(request):
        raise RequestError("bad request %r: expected '<keyword>: <details>', like 'add: bathroom' or "
                           "'build: living room, kitchen, bedroom x2, bathroom'" % request)
    return request


def build_prompt(layout_text: str, request: str, template: Optional[str] = None, hallways: bool = False) -> str:
    """The layout text is re-printed in canonical form, so a malformed layout fails here, not in the agent."""
    layout = format_layout(parse_layout(layout_text))
    if template is None:
        template = (HALLWAYS_TEMPLATE_PATH if hallways else TEMPLATE_PATH).read_text().rstrip("\n")
    return template.replace("{{LAYOUT}}", layout).replace("{{REQUEST}}", check_request(request))


def fetch_layout(server: str) -> str:
    with urllib.request.urlopen(server.rstrip("/") + "/layout", timeout=5) as response:
        return response.read().decode("utf-8")


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Print the agent prompt for one request")
    parser.add_argument("request", help="'<keyword>: <details>', like 'add: bathroom'")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--layout", type=Path, help="layout file to use")
    source.add_argument("--empty", action="store_true", help="use an empty grid")
    parser.add_argument("--server", default="http://127.0.0.1:8000", help="where to get the current layout")
    parser.add_argument("--hallways", action="store_true", help="the prompt for a run that allows hallways")
    args = parser.parse_args(argv)
    try:
        if args.empty:
            layout_text = empty_layout_text()
        elif args.layout:
            layout_text = args.layout.read_text()
        else:
            layout_text = fetch_layout(args.server)
        print(build_prompt(layout_text, args.request, hallways=args.hallways))
    except (RequestError, ValueError, OSError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
