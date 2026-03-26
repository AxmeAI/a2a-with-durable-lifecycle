"""
A2A with durable lifecycle - Python example.

Dispatcher agent sends a task to an executor agent via AXME.
AXME handles delivery, retries, and lifecycle tracking.
No custom retry logic, no polling, no message queues.

Usage:
    pip install axme
    export AXME_API_KEY="your-key"
    python main.py
"""

import os
from axme import AxmeClient, AxmeClientConfig


def main():
    client = AxmeClient(
        AxmeClientConfig(api_key=os.environ["AXME_API_KEY"])
    )

    # Dispatch a task to the executor agent
    intent_id = client.send_intent(
        {
            "intent_type": "intent.a2a.task_execution.v1",
            "to_agent": "agent://myorg/production/a2a-executor",
            "payload": {
                "task_id": "TASK-2026-0042",
                "task_type": "data_enrichment",
                "source_agent": "dispatcher-agent",
                "input_data": {
                    "records": 5000,
                    "enrichment": "geo_lookup",
                },
                "priority": "normal",
            },
        }
    )
    print(f"Task dispatched: {intent_id}")

    # Observe lifecycle - AXME handles retries and delivery
    print("Watching lifecycle...")
    for event in client.observe(intent_id):
        status = event.get("status", "")
        print(f"  [{status}] {event.get('event_type', '')}")
        if status in ("COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"):
            break

    intent = client.get_intent(intent_id)
    print(f"\nFinal status: {intent['intent']['lifecycle_status']}")


if __name__ == "__main__":
    main()
