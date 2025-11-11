"""Activities for invoking Ray Serve inference endpoints via HTTP.

This module defines Pydantic models and an activity that sends
inference requests to a Ray Serve deployment over HTTP and returns
structured results.
"""

from __future__ import annotations

from typing import Any

import aiohttp
from pydantic import ValidationError
from temporalio import activity
from src.workflows.serve_inference.types import (
    InferenceRequest,
    InferenceResponse,
)

async def _post_json(url: str, json_payload: dict[str, Any], timeout: float) -> tuple[int, Any]:
    """Helper to POST JSON and parse JSON response.

    Returns an (status_code, json_data_or_text) tuple. This function is kept
    separate to simplify mocking in tests.
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_payload, timeout=timeout) as resp:
            status = resp.status
            # Try JSON first; fall back to text for debugging
            try:
                data = await resp.json()
            except Exception:  # noqa: BLE001
                data = await resp.text()
            return status, data

@activity.defn
async def call_serve_inference(request: InferenceRequest) -> InferenceResponse:
    """Activity that invokes a Ray Serve endpoint over HTTP.

    This activity performs the non-deterministic network I/O, so it should be
    invoked from workflows using `workflow.execute_activity` with appropriate
    timeouts and retry policies.
    """
    full_url = f"{str(request.endpoint_url).rstrip('/')}{request.route}"
    activity.logger.info("Calling Ray Serve at %s", full_url)

    try:
        status, data = await _post_json(full_url, request.payload, request.timeout_seconds)
        if status >= 200 and status < 300:
            # Validate JSON shape into dict[str, Any] via Pydantic
            try:
                parsed = data if isinstance(data, dict) else {"raw": data}
                return InferenceResponse(status_code=status, output=parsed)
            except ValidationError as ve:  # pragma: no cover
                return InferenceResponse(status_code=status, error=str(ve))
        return InferenceResponse(status_code=status, error=str(data))
    except Exception as exc:  # noqa: BLE001
        activity.logger.exception("Ray Serve inference call failed: %s", exc)
        return InferenceResponse(status_code=599, error=str(exc))
