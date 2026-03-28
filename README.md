# A2A with Durable Lifecycle

A2A protocol enables agent communication. AXME adds what's missing - durable lifecycle, retries, timeouts, and human checkpoints.

A2A defines how agents talk to each other. But talking is not enough. When Agent B crashes mid-task, who retries? When Agent B needs a human decision, who manages the wait? A2A is a communication protocol - it handles the message. AXME is a lifecycle protocol - it handles everything after the message arrives.

> **Alpha** - Built with [AXME](https://github.com/AxmeAI/axme) (AXP Intent Protocol).
> [cloud.axme.ai](https://cloud.axme.ai) - [hello@axme.ai](mailto:hello@axme.ai)

---

## The Problem

A2A handles communication between agents. But communication alone is not lifecycle management:

- **Agent B crashes mid-task** - A2A does not know. The task is lost.
- **Agent B needs human input** - A2A has no approval gate. You build it yourself.
- **Agent B is slow** - A2A has no timeout. You poll forever.
- **Network drops the message** - A2A has no retry. You write retry logic.

Every team ends up building the same retry/timeout/approval infrastructure on top of A2A. That infrastructure is what AXME provides.

### Raw A2A (manual retry, no lifecycle)

```python
# Dispatcher sends task to executor via HTTP
import httpx, time

max_retries = 3
for attempt in range(max_retries):
    try:
        resp = httpx.post("https://executor-agent/tasks", json={
            "task_id": "TASK-2026-0042",
            "task_type": "data_enrichment",
            "input_data": {"records": 5000, "enrichment": "geo_lookup"},
        })
        resp.raise_for_status()
        break
    except httpx.HTTPError:
        if attempt == max_retries - 1:
            raise
        time.sleep(2 ** attempt)

# Poll for result (no lifecycle tracking)
while True:
    status = httpx.get(f"https://executor-agent/tasks/TASK-2026-0042").json()
    if status["state"] in ("completed", "failed"):
        break
    time.sleep(5)  # How long? Forever?
```

### AXME (durable lifecycle, 4 lines)

```python
intent_id = client.send_intent({
    "intent_type": "intent.a2a.task_execution.v1",
    "to_agent": "agent://myorg/production/a2a-executor",
    "payload": {"task_id": "TASK-2026-0042", "task_type": "data_enrichment"},
})
result = client.wait_for(intent_id)
```

AXME handles retries (3 attempts), timeouts (120s deadline), delivery confirmation, and lifecycle tracking. If the executor crashes, AXME retries. If it times out, the dispatcher knows.

---

## Quick Start

### Python

```bash
pip install axme
export AXME_API_KEY="your-key"   # Get one: axme login
```

```python
from axme import AxmeClient, AxmeClientConfig
import os

client = AxmeClient(AxmeClientConfig(api_key=os.environ["AXME_API_KEY"]))

intent_id = client.send_intent({
    "intent_type": "intent.a2a.task_execution.v1",
    "to_agent": "agent://myorg/production/a2a-executor",
    "payload": {
        "task_id": "TASK-2026-0042",
        "task_type": "data_enrichment",
        "source_agent": "dispatcher-agent",
        "input_data": {"records": 5000, "enrichment": "geo_lookup"},
        "priority": "normal",
    },
})

print(f"Dispatched: {intent_id}")
result = client.wait_for(intent_id)
print(f"Done: {result['status']}")
```

### TypeScript

```bash
npm install @axme/axme
```

```typescript
import { AxmeClient } from "@axme/axme";

const client = new AxmeClient({ apiKey: process.env.AXME_API_KEY! });

const intentId = await client.sendIntent({
  intentType: "intent.a2a.task_execution.v1",
  toAgent: "agent://myorg/production/a2a-executor",
  payload: {
    taskId: "TASK-2026-0042",
    taskType: "data_enrichment",
    sourceAgent: "dispatcher-agent",
    inputData: { records: 5000, enrichment: "geo_lookup" },
    priority: "normal",
  },
});

console.log(`Dispatched: ${intentId}`);
const result = await client.waitFor(intentId);
console.log(`Done: ${result.status}`);
```

---

## More Languages

| Language | Directory | Install |
|----------|-----------|---------|
| [Python](python/) | `python/` | `pip install axme` |
| [TypeScript](typescript/) | `typescript/` | `npm install @axme/axme` |

---

## How It Works

```
+-----------+  send_intent()   +----------------+  deliver    +-----------+
|           | ---------------> |                | ----------> |           |
| Dispatcher|                  |   AXME Cloud   |             | Executor  |
|  (agent)  | <- wait_for() -- |   (platform)   | <- result   |  (agent)  |
|           |                  |                |             |           |
|           |                  |  - 3 retries   |             +-----------+
|           |                  |  - 120s timeout|
|           | <- COMPLETED --- |  - lifecycle   |
|           |                  |  - audit trail |
+-----------+                  +----------------+
```

1. Dispatcher sends a **task intent** with enrichment parameters
2. AXME **delivers** the intent to the executor agent (with retries)
3. Executor **processes** the task (geo lookup on 5000 records)
4. Executor **resumes** the intent with results (records processed, success rate)
5. Dispatcher gets the **final result** via lifecycle tracking
6. If executor crashes, AXME **retries** delivery (up to 3 attempts)

---

## Run the Full Example

### Prerequisites

```bash
# Install CLI (one-time)
curl -fsSL https://raw.githubusercontent.com/AxmeAI/axme-cli/main/install.sh | sh
# Open a new terminal, or run the "source" command shown by the installer

# Log in
axme login

# Install Python SDK
pip install axme
```

### Terminal 1 - submit the scenario

```bash
axme scenarios apply scenario.json
# Note the intent_id in the output
```

### Terminal 2 - start the executor agent

Get the agent key after scenario apply:

```bash
# macOS
cat ~/Library/Application\ Support/axme/scenario-agents.json | grep -A2 a2a-executor-demo

# Linux
cat ~/.config/axme/scenario-agents.json | grep -A2 a2a-executor-demo
```

Run in your language of choice:

```bash
# Python
AXME_API_KEY=<agent-key> python agent.py

# TypeScript (requires Node 20+)
cd typescript && npm install
AXME_API_KEY=<agent-key> npx tsx agent.ts
```

### Verify

```bash
axme intents get <intent_id>
# lifecycle_status: COMPLETED
```

---

## Related

- [AXME](https://github.com/AxmeAI/axme) - project overview
- [AXP Spec](https://github.com/AxmeAI/axp-spec) - open Intent Protocol specification
- [AXME Examples](https://github.com/AxmeAI/axme-examples) - 20+ runnable examples across 5 languages
- [AXME CLI](https://github.com/AxmeAI/axme-cli) - manage intents, agents, scenarios from the terminal
- [Durable Execution with Human Approval](https://github.com/AxmeAI/durable-execution-with-human-approval) - human approval gates

---

Built with [AXME](https://github.com/AxmeAI/axme) (AXP Intent Protocol).
