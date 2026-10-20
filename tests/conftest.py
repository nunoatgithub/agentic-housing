from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


@pytest.fixture
def example_text() -> str:
    """The example layout from HOUSE_DSL.md, byte for byte, without a trailing newline."""
    return (DATA / "example_layout.txt").read_text().rstrip("\n")
