import json

import pytest

from house.copilot_agent import parse_copilot_output


def test_copilot_jsonl_response_preserves_text_and_usage_events():
    output = "\n".join([
        json.dumps({"type": "session.start", "data": {"sessionId": "session-1"}}),
        json.dumps({"type": "assistant.message", "data": {"content": "room R1 living room A1"}}),
        json.dumps({"type": "session.usage", "data": {"ai_credits": 1.5}}),
    ])

    reply = parse_copilot_output(output)

    assert reply.text == "room R1 living room A1"
    assert reply.usage["cost_usd"] is None
    assert reply.metadata == {
        "copilot_usage_events": [{"type": "session.usage", "data": {"ai_credits": 1.5}}]
    }


def test_copilot_jsonl_response_rejects_missing_assistant_text():
    with pytest.raises(RuntimeError, match="no assistant message"):
        parse_copilot_output(json.dumps({"type": "session.idle", "data": {}}))


def test_copilot_jsonl_response_surfaces_session_errors():
    output = json.dumps({"type": "session.error", "data": {"message": "model unavailable"}})

    with pytest.raises(RuntimeError, match="model unavailable"):
        parse_copilot_output(output)
