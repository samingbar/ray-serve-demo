# Temporal + Ray Serve Inference

This example demonstrates how to orchestrate batch inference using Temporal workflows while delegating HTTP inference calls to a Ray Serve deployment. Temporal provides reliability, retries, and parallel orchestration; Ray Serve provides scalable model serving.

## Components

- Workflow: `src/workflows/serve_inference/serve_inference_workflow.py`
- Activities: `src/workflows/serve_inference/serve_inference_activities.py`
- Worker: `src/workflows/serve_inference/worker.py`

## Ray Serve quick start

Run a minimal Ray Serve deployment that echoes the request payload. In a separate shell:

```python
# save as serve_app.py
import ray
from ray import serve
from starlette.requests import Request


@serve.deployment(num_replicas=1, route_prefix="/inference")
class EchoModel:
    async def __call__(self, request: Request):
        data = await request.json()
        # Simulate inference by echoing the payload
        return {"prediction": data}


if __name__ == "__main__":
    ray.init()
    serve.start(detached=False)  # Start Serve on http://127.0.0.1:8000
    EchoModel.deploy()
    print("Ray Serve started at http://127.0.0.1:8000/inference")
    import time

    while True:
        time.sleep(60)
```

Run it with:

```bash
python serve_app.py
```

Alternatively, deploy your own model that accepts POST JSON at `/inference` and returns JSON.

## Start Temporal worker

In another terminal, start the worker that registers the workflow and activity:

```bash
uv run -m src.workflows.serve_inference.worker
```

## Execute the workflow

You can run the workflow’s `main()` directly, or use a Temporal client. Using the provided `main()`:

```bash
uv run -m src.workflows.serve_inference.serve_inference_workflow
```

This sends two requests to `http://localhost:8000/inference` in parallel and aggregates responses.

## Patterns shown

- Fan-out/fan-in orchestration using `asyncio.gather` within a workflow
- Activities encapsulate non-deterministic HTTP I/O
- Pydantic models for validated inputs/outputs
- Tests with mocked activities and patched HTTP helper

## Notes

- The workflow calls the activity with a per-request timeout. Add retries at the workflow level if desired.
- For production, run Ray Serve in a separate cluster and authenticate the endpoint; keep secrets in environment variables and inject via activity configuration.

