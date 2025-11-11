"""Minimal Ray Serve app for testing Temporal integration.

This app exposes a simple echo model at ``/inference`` and enables basic
autoscaling. It is intentionally lightweight so you can replace ``EchoModel``
with your real model while reusing the Serve configuration skeleton.
"""

from __future__ import annotations

import asyncio
import signal
import sys

import ray
from ray import serve
from starlette.requests import Request

# Basic Ray-managed inference autoscaling
@serve.deployment(
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 5,
        # Scale when each replica has ~8 concurrent requests in-flight
        "target_num_ongoing_requests_per_replica": 8,
    },
)

class EchoModel:
    """Echo the JSON payload to simulate an inference response."""

    async def __call__(self, request: Request):
        data = await request.json()
        return {"prediction": data}


# Main Application Function
async def main():
    """Initialize Ray + Serve, deploy the model, and wait for shutdown.

    The deployment is bound to the route prefix ``/inference``. Shutdown is
    handled gracefully on SIGINT/SIGTERM.
    """

    ray.init()
    serve.start(detached=False)

    # Runs Echo Model, which will echo back the input for testing
    serve.run(EchoModel.bind(), route_prefix="/inference")

    print("✅ Ray Serve started at http://127.0.0.1:8000/inference")

    # Handle graceful shutdown
    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(sig, stop_event.set)


    await stop_event.wait()
    print("🧹 Shutting down Ray Serve...")
    serve.shutdown()
    ray.shutdown()
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
