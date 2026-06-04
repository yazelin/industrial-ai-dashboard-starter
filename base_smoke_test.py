#!/usr/bin/env python3
"""Base smoke (no extra): the built-in simulator produces the expected shape and
the rule-based summary is deterministic. No TestClient (base has no httpx).
Exits non-zero on failure."""
import sys
from app.data_source import simulated_snapshot
from app.summary import rule_summary

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

snap = simulated_snapshot()
check({"agvs", "machines", "alerts", "timestamp"} <= set(snap), f"snapshot shape (got {sorted(snap)})")
check(isinstance(snap["agvs"], list) and len(snap["agvs"]) >= 1, "snapshot has agvs")

fixed = {"agvs": [{"id": "AGV-1", "battery": 88}, {"id": "AGV-2", "battery": 10}],
         "machines": [{"id": "AOI-1", "status": "run"}, {"id": "PLC-2", "status": "stop"}],
         "alerts": [{"level": "warning"}]}
r = rule_summary(fixed)
for piece in ["AGV 2 台在線", "低電量 1 台", "AGV-2", "異常機台 1 台", "PLC-2", "告警 1 則"]:
    check(piece in r, f"rule_summary contains {piece!r} (got {r!r})")

if failures:
    print("FAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print("OK: base smoke passed (simulator shape + deterministic rule summary)")
