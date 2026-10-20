from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


@pytest.fixture
def example_text() -> str:
    """A five-room house for the tests, without a trailing newline. A second living room at B1 serves the bedroom
    and bathroom (it was a hallway before the language dropped hallways; the scores are the same)."""
    return (DATA / "example_layout.txt").read_text().rstrip("\n")
