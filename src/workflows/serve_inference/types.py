from __future__ import annotations

from typing import Any

from pydantic import BaseModel, HttpUrl

class BatchInferenceItem(BaseModel):
    """A single item to be sent to the model for inference."""

    payload: dict
    """JSON-serializable payload for the model."""


class BatchInferenceInput(BaseModel):
    """Input model for batch inference orchestration."""

    endpoint_url: HttpUrl
    """Base URL of the Ray Serve endpoint (e.g., http://localhost:8000)."""

    route: str = "/inference"
    """Relative route accepting POST requests."""

    items: list[BatchInferenceItem]
    """List of items to infer in parallel."""

    per_request_timeout_seconds: float = 5.0
    """Timeout for each underlying activity HTTP request."""

class BatchInferenceOutput(BaseModel):
    """Aggregated output for batch inference."""

    results: list[InferenceResponse]
    """One result per requested input item, preserving order."""


class InferenceRequest(BaseModel):
    """Input model for a single inference request to Ray Serve."""

    endpoint_url: HttpUrl
    """Base URL of the Ray Serve endpoint (e.g., http://localhost:8000)."""

    route: str = "/inference"
    """Relative route on the endpoint that accepts POST requests."""

    payload: dict[str, Any]
    """JSON payload to send to the model (must be JSON-serializable)."""

    timeout_seconds: float = 5.0
    """Request timeout for the HTTP call."""


class InferenceResponse(BaseModel):
    """Output model for a single inference response from Ray Serve."""

    status_code: int
    """HTTP status code returned by the endpoint."""

    output: dict[str, Any] | None = None
    """Parsed JSON output from the model, if available."""

    error: str | None = None
    """Error message, if the request failed or response was invalid."""
