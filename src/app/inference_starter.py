
import asyncio
import json
import sys
import uuid
from pathlib import Path

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

# Support running as a script (file path) by adding project root to sys.path
try:
    from src.workflows.serve_inference.types import (
        BatchInferenceInput,
        BatchInferenceItem,
    )
except ModuleNotFoundError:  # pragma: no cover - convenience for script runs
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from src.workflows.serve_inference.types import (
        BatchInferenceInput,
        BatchInferenceItem,
    )


async def main() -> None: 
    """Trigger a basic inference workflow.

    Steps
    1. Read sample inputs (JSON list of payloads) from the local file.
    2. Connect to Temporal using the Pydantic data converter.
    3. Execute the workflow against ``serve-inference-task-queue``.
    """
    json_path = Path(__file__).with_name("text_pairs_500.json")
    with json_path.open("r") as file:
        tests = json.load(file)

    items = [BatchInferenceItem(payload = test) for test in tests]

    client = await Client.connect("localhost:7233", data_converter=pydantic_data_converter)
    input_data = BatchInferenceInput(
        endpoint_url="http://localhost:8000",
        route="/inference",
        items=items
    )
    result = await client.execute_workflow(
        "ServeBatchInferenceWorkflow",
        input_data,
        id=f"serve-batch-inference-{uuid.uuid4()}",
        task_queue="serve-inference-task-queue",
    )
    print(result)  

if __name__ == "__main__":
    asyncio.run(main())
"""Simple CLI to trigger the ServeBatchInferenceWorkflow with sample inputs.

This script loads a small set of test payloads from ``text_pairs_500.json`` and
submits them as a batch to the Temporal workflow. It can be executed either as
``python -m src.app.inference_starter`` or directly via file path.
"""
