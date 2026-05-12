"""Mock LLM API server for offline book reading.

Returns pre-recorded responses so readers can run all examples
without any API key.

Usage:
    python mock/mock_server.py          # starts on localhost:9999
    MOCK=1 python ch02-hello-agent/weather_agent.py
"""
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

RESPONSES_DIR = Path(__file__).parent / "responses"

# Route: request content keyword → response file
# Matched in order; first match wins
ROUTES = [
    # ch02 weather agent: first request (user asks about weather)
    ("get_weather", "ch02_weather_tool.json"),
    # ch02 weather agent: second request (after tool result returned)
    ("晴，25°C", "ch02_weather_answer.json"),
    # ch09 structured output
    ("UserInfo", "ch09_structured.json"),
    # ch01 general LLM Q&A
    ("大语言模型", "ch01_general.json"),
]


class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else "{}"

        # Find matching response file
        resp_file = None
        for keyword, filename in ROUTES:
            if keyword in body:
                resp_file = RESPONSES_DIR / filename
                break

        if resp_file and resp_file.exists():
            data = json.loads(resp_file.read_text())
            # Simulate streaming: send as SSE if stream=true in request
            if '"stream":true' in body or '"stream": true' in body:
                self._send_stream(data)
            else:
                self._send_json(data)
        else:
            # Fallback: return a generic completion
            self._send_json({
                "id": "mock-fallback",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "mock",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": (
                            "[Mock 模式] 这是一个模拟的 LLM 响应。"
                            "在你的实际环境中，这里会是真实模型的回复。"
                        ),
                    },
                    "finish_reason": "stop",
                }],
            })

    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _send_stream(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        content = data["choices"][0]["message"]["content"]
        for chunk in content.split():  # simple word-by-word streaming
            sse = f"data: {json.dumps({'choices': [{'delta': {'content': chunk + ' '}}]})}\n\n"
            self.wfile.write(sse.encode())
            self.wfile.flush()
            time.sleep(0.05)
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, format, *args):
        print(f"  [mock] {args[0]}")


if __name__ == "__main__":
    print("AgentScope Book Lab Mock Server")
    print("  Listening on http://127.0.0.1:9999")
    print("  Responses dir:", RESPONSES_DIR)
    print("  Press Ctrl+C to stop\n")
    HTTPServer(("127.0.0.1", 9999), MockHandler).serve_forever()
