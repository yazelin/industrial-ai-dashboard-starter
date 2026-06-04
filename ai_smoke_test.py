#!/usr/bin/env python3
"""AI summary smoke (needs the `ai` extra). rule_summary is deterministic; the
LLM summary is wired through an OpenAI-compatible endpoint, verified against a
local fake OpenAI server (no API key). The ai extra brings httpx, so TestClient
is available here. Exits non-zero on failure."""
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

CANNED = "今日 3 台 AGV 正常運作，1 則低電量告警已處理。"

class _Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"choices": [{"message": {"content": CANNED}}]}).encode())
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", 0), _Fake)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

# Set before importing app.main (config reads env live, but be explicit).
os.environ["AI_SUMMARY"] = "llm"
os.environ["HTTP_LLM_ENDPOINT"] = f"http://127.0.0.1:{port}/v1/chat/completions"

from starlette.testclient import TestClient
from app.main import app
from app.summary import rule_summary

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

check("AGV 1 台在線" in rule_summary({"agvs": [{"id": "AGV-1", "battery": 50}], "machines": [], "alerts": []}),
      "rule_summary deterministic")

try:
    out = TestClient(app).get("/api/ai-summary").json()["summary"]
    check(out == CANNED, f"/api/ai-summary llm -> fake server content (got {out!r})")
finally:
    srv.shutdown()

if failures:
    print("FAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print("OK: AI summary smoke passed (rule deterministic + llm wired)")
