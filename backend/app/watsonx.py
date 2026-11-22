"""IBM watsonx.ai Granite explanation adapter.

The deterministic MomentGuard engine remains the safety authority. This module only
generates a grounded human-readable explanation after the decision has already been made.
"""
from __future__ import annotations

import time
from time import perf_counter
import httpx

_TOKEN_CACHE = {"token": None, "expires_at": 0.0}


def configured(settings) -> bool:
    return bool(settings.watsonx_configured)


def build_explanation_messages(snapshot: dict) -> list[dict]:
    rec = snapshot["recommendation"]
    state = snapshot["state"]
    fan = snapshot["fan"]
    calc = rec.get("calculation") or {}
    safe = rec.get("safeWindow") or {}
    system = (
        "You are the explanation layer for MomentGuard AI. "
        "The deterministic MomentGuard safety engine has already made the final decision. "
        "You MUST NOT change the action or destination. Explain the decision in 1-2 concise sentences, "
        "using only the supplied facts. Do not invent statistics, probabilities, venue facts, or game events."
    )
    facts = {
        "action": rec.get("action"),
        "destination": rec.get("destination"),
        "recommendedMode": rec.get("recommendedMode"),
        "momentRisk": rec.get("riskScore"),
        "riskScale": rec.get("riskScale"),
        "reason": rec.get("reason"),
        "score": f"{state.get('scoreA')}-{state.get('scoreB')}",
        "quarter": state.get("quarter"),
        "clock": state.get("clock"),
        "scenario": state.get("scenario"),
        "availableWindowMinutes": safe.get("availableMinutes", state.get("availableWindowMinutes")),
        "requiredTripMinutes": safe.get("requiredMinutes", rec.get("roundTripMinutes")),
        "safetyMarginMinutes": safe.get("marginMinutes"),
        "need": fan.get("need"),
        "accessible": fan.get("accessible"),
        "seatDeliveryEnabled": fan.get("delivery"),
        "selectedFacility": calc.get("name"),
    }
    user = "MomentGuard evidence:\n" + "\n".join(f"- {k}: {v}" for k, v in facts.items() if v is not None)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


async def _iam_token(settings, client: httpx.AsyncClient) -> str:
    now = time.time()
    if _TOKEN_CACHE["token"] and now < _TOKEN_CACHE["expires_at"] - 60:
        return _TOKEN_CACHE["token"]
    response = await client.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": settings.watsonx_api_key,
        },
    )
    response.raise_for_status()
    payload = response.json()
    token = payload["access_token"]
    expiration = float(payload.get("expiration", now + 3600))
    _TOKEN_CACHE.update(token=token, expires_at=expiration)
    return token


async def generate_granite_explanation(snapshot: dict, settings, transport=None) -> dict:
    if not configured(settings):
        raise ValueError("IBM watsonx.ai is not configured. Add WATSONX_API_KEY, WATSONX_PROJECT_ID and WATSONX_MODEL_ID to backend/.env.")

    timeout = httpx.Timeout(settings.agent_timeout_seconds)
    started = perf_counter()
    async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
        token = await _iam_token(settings, client)
        url = settings.watsonx_url.rstrip("/") + "/ml/v1/text/chat"
        response = await client.post(
            url,
            params={"version": settings.watsonx_api_version},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
            json={
                "model_id": settings.watsonx_model_id,
                "project_id": settings.watsonx_project_id,
                "messages": build_explanation_messages(snapshot),
                "max_tokens": settings.watsonx_max_tokens,
                "temperature": 0.1,
            },
        )
        response.raise_for_status()
        payload = response.json()

    choices = payload.get("choices") or []
    if not choices:
        raise ValueError("watsonx.ai returned no explanation choices")
    content = choices[0].get("message", {}).get("content")
    if isinstance(content, list):
        content = " ".join(str(item.get("text", "")) if isinstance(item, dict) else str(item) for item in content).strip()
    content = str(content or "").strip()
    if not content:
        raise ValueError("watsonx.ai returned an empty explanation")
    return {
        "explanation": content,
        "provider": "IBM watsonx.ai / Granite",
        "model": payload.get("model_id") or payload.get("model") or settings.watsonx_model_id,
        "latencyMs": round((perf_counter() - started) * 1000, 2),
        "usage": payload.get("usage"),
    }
