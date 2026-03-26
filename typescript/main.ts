/**
 * A2A with durable lifecycle - TypeScript example.
 *
 * Dispatcher sends a task to an executor agent via AXME.
 * AXME handles delivery, retries, and lifecycle tracking.
 * No custom retry logic, no polling, no message queues.
 *
 * Usage:
 *   npm install @axme/axme
 *   export AXME_API_KEY="your-key"
 *   npx tsx main.ts
 */

import { AxmeClient } from "@axme/axme";

async function main() {
  const client = new AxmeClient({ apiKey: process.env.AXME_API_KEY! });

  const intentId = await client.sendIntent({
    intentType: "intent.a2a.task_execution.v1",
    toAgent: "agent://myorg/production/a2a-executor",
    payload: {
      taskId: "TASK-2026-0042",
      taskType: "data_enrichment",
      sourceAgent: "dispatcher-agent",
      inputData: {
        records: 5000,
        enrichment: "geo_lookup",
      },
      priority: "normal",
    },
  });
  console.log(`Task dispatched: ${intentId}`);

  const result = await client.waitFor(intentId);
  console.log(`Final status: ${result.status}`);
}

main().catch(console.error);
