"""Workflow that orchestrates batch inference via Ray Serve activities.

This workflow demonstrates combining Temporal with Ray Serve by delegating
HTTP inference calls to activities and orchestrating fan-out/fan-in execution
for batch inputs.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from temporalio import workflow
from src.workflows.serve_inference.serve_inference_activities import (
    call_serve_inference,
)
from src.workflows.serve_inference.types import (
    BatchInferenceInput,
    BatchInferenceItem,
    BatchInferenceOutput,
    InferenceRequest,
    InferenceResponse,
)

@workflow.defn
class ServeBatchInferenceWorkflow:
    """Orchestrates parallel Ray Serve calls via activities and aggregates results."""

    @workflow.run
    async def run(self, input: BatchInferenceInput) -> BatchInferenceOutput:  # noqa: A002
        """Run the batch inference orchestration."""
        workflow.logger.info(
            "Starting batch inference for %d item(s) via %s%s",
            len(input.items),
            input.endpoint_url,
            input.route,
        )

        async def one_call(item: BatchInferenceItem) -> InferenceResponse:
            req = InferenceRequest(
                endpoint_url=input.endpoint_url,
                route=input.route,
                payload=item.payload,
                timeout_seconds=input.per_request_timeout_seconds,
            )
            return await workflow.execute_activity(
                call_serve_inference,
                req,
                start_to_close_timeout=timedelta(seconds=max(1, int(input.per_request_timeout_seconds) + 2)),
            )

        # Fan-out and gather preserving order
        tasks = [one_call(item) for item in input.items]
        results: list[InferenceResponse] = await asyncio.gather(*tasks)
        return BatchInferenceOutput(results=results)



