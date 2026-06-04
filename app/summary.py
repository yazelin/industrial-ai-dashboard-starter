"""AI summary — Part 2 axis B. rule_summary is the deterministic baseline (it
replaces the old one-line stub); llm_summary is the LLM 班報 upgrade and needs
the `ai` extra. The /api/ai-summary endpoint picks via AI_SUMMARY (rule|llm)."""
import json


def rule_summary(snapshot) -> str:
    """Deterministic rule-based shift report from a dashboard snapshot."""
    agvs = snapshot.get("agvs", [])
    machines = snapshot.get("machines", [])
    alerts = snapshot.get("alerts", [])
    low = [a["id"] for a in agvs if a.get("battery", 100) < 20]
    abnormal = [m["id"] for m in machines if m.get("status") not in ("run", None)]
    parts = [
        f"AGV {len(agvs)} 台在線",
        f"低電量 {len(low)} 台" + (f"({'/'.join(low)})" if low else ""),
        f"異常機台 {len(abnormal)} 台" + (f"({'/'.join(abnormal)})" if abnormal else ""),
        f"告警 {len(alerts)} 則",
    ]
    return "；".join(parts) + "。"


async def llm_summary(snapshot) -> str:
    """LLM shift report via an OpenAI-compatible endpoint. Requires the `ai`
    extra (httpx, imported lazily so the base install stays httpx-free)."""
    import httpx
    from . import config
    payload = {
        "model": config.model_name(),
        "messages": [
            {"role": "system", "content": "你是工廠夜班主管，用繁體中文寫一句簡短班報。"},
            {"role": "user", "content": "現場快照:\n" + json.dumps(snapshot, ensure_ascii=False)},
        ],
    }
    headers = {"Authorization": "Bearer " + (config.llm_api_key() or "x")}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(config.llm_endpoint(), json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
