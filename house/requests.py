"""Structured requests: 'build: living room, kitchen, bedroom x2, bathroom' or 'add: bedroom x2, bathroom'."""
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

from .model import ROOM_TYPES

_REQUEST = re.compile(r"(build|add): (.+)")
_ITEM = re.compile(r"\s*(.+?)(?: [x×] ?(\d+))?\s*")


def parse_request(text: Optional[str]) -> Optional[Tuple[str, Dict[str, int]]]:
    """('build' or 'add', rooms asked for by type), or None if the text is not a request of that shape."""
    m = _REQUEST.fullmatch(" ".join((text or "").split()))
    if not m:
        return None
    counts: Dict[str, int] = {}
    for item in m[2].split(","):
        parsed = _ITEM.fullmatch(item)
        if not parsed or parsed[1] not in ROOM_TYPES:
            return None
        counts[parsed[1]] = counts.get(parsed[1], 0) + int(parsed[2] or 1)
    return m[1], counts
