import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from house.deepseek_agent import ask_deepseek, cost_usd


class Handler(BaseHTTPRequestHandler):
    body = None
    headers = None

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        Handler.body = self.rfile.read(n)
        Handler.headers = dict(self.headers)
        payload = {"id": "msg_test", "type": "message", "role": "assistant", "model": "deepseek-flash",
                   "content": [{"type": "text", "text": "room R5 bedroom B2\ndoor B1|B2"}],
                   "stop_reason": "end_turn",
                   "usage": {"input_tokens": 100, "output_tokens": 10, "cache_read_input_tokens": 0}}
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_api(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "http://127.0.0.1:%d/anthropic" % server.server_address[1])
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


def test_ask_deepseek_sends_the_clean_no_thinking_request(fake_api):
    reply = ask_deepseek("PROMPT")
    body = json.loads(Handler.body)
    assert body["model"] == "deepseek-flash"
    assert body["system"] == "You are a helpful assistant."
    assert body["messages"] == [{"role": "user", "content": "PROMPT"}]
    assert body["thinking"] == {"type": "disabled"}
    assert "output_config" not in body
    assert "environment" not in body["system"].lower()
    assert Handler.headers["Authorization"] == "Bearer test-key"
    assert reply.text == "room R5 bedroom B2\ndoor B1|B2"
    assert reply.usage["output_tokens"] == 10
    assert reply.usage["cost_usd"] > 0
    assert reply.cut_off is False


def test_ask_deepseek_can_request_low_thinking(fake_api):
    ask_deepseek("PROMPT", effort="low")
    body = json.loads(Handler.body)
    assert body["thinking"] == {"type": "enabled"}
    assert body["output_config"] == {"effort": "low"}


def test_deepseek_cost_uses_the_off_peak_and_peak_prices():
    saturday_noon = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)
    friday_0200 = datetime(2026, 11, 6, 2, 0, tzinfo=timezone.utc)
    assert cost_usd(1_000_000, 0, 1_000_000, at=saturday_noon) == 0.75
    assert cost_usd(1_000_000, 0, 1_000_000, at=friday_0200) == 1.5
