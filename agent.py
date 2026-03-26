"""
Task executor agent - receives and executes tasks from other agents via A2A.

Listens for intents via SSE. Simulates data enrichment work
(geo lookup on records) and resumes with execution results.
AXME handles retries if this agent crashes mid-task.

Usage:
    export AXME_API_KEY="<agent-key>"
    python agent.py
"""

import os
import sys
import time

sys.stdout.reconfigure(line_buffering=True)

from axme import AxmeClient, AxmeClientConfig


AGENT_ADDRESS = "a2a-executor-demo"


def handle_intent(client, intent_id):
    """Execute a task dispatched from another agent."""
    intent_data = client.get_intent(intent_id)
    intent = intent_data.get("intent", intent_data)
    payload = intent.get("payload", {})
    if "parent_payload" in payload:
        payload = payload["parent_payload"]

    task_id = payload.get("task_id", "unknown")
    task_type = payload.get("task_type", "unknown")
    source_agent = payload.get("source_agent", "unknown")
    input_data = payload.get("input_data", {})
    records = input_data.get("records", 0)
    enrichment = input_data.get("enrichment", "unknown")

    print(f"  Receiving task from dispatcher ({source_agent})...")
    print(f"  Task: {task_id} ({task_type})")
    time.sleep(1)

    print(f"  Enriching {records} records with geo data...")
    time.sleep(2)

    print(f"  Enrichment complete.")
    time.sleep(1)

    result = {
        "action": "complete",
        "task_id": task_id,
        "records_processed": records,
        "enrichment_applied": enrichment,
        "success_rate": 0.98,
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    client.resume_intent(intent_id, result)
    print(f"  Task {task_id} completed. {records} records enriched ({enrichment}).")
    print(f"  Result sent back to dispatcher via AXME.")


def main():
    api_key = os.environ.get("AXME_API_KEY", "")
    if not api_key:
        print("Error: AXME_API_KEY not set.")
        print("Run the scenario first: axme scenarios apply scenario.json")
        print("Then get the agent key from ~/.config/axme/scenario-agents.json")
        sys.exit(1)

    client = AxmeClient(AxmeClientConfig(api_key=api_key))

    print(f"Agent listening on {AGENT_ADDRESS}...")
    print("Waiting for intents (Ctrl+C to stop)\n")

    for delivery in client.listen(AGENT_ADDRESS):
        intent_id = delivery.get("intent_id", "")
        status = delivery.get("status", "")

        if not intent_id:
            continue

        if status in ("DELIVERED", "CREATED", "IN_PROGRESS"):
            print(f"[{status}] Intent received: {intent_id}")
            try:
                handle_intent(client, intent_id)
            except Exception as e:
                print(f"  Error processing intent: {e}")


if __name__ == "__main__":
    main()
