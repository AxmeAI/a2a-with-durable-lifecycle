/**
 * Task executor agent - TypeScript example.
 *
 * Listens for intents via SSE, executes tasks dispatched from
 * other agents, resumes with execution results.
 * AXME handles retries if this agent crashes mid-task.
 *
 * Usage:
 *   export AXME_API_KEY="<agent-key>"
 *   npx tsx agent.ts
 */

import { AxmeClient } from "@axme/axme";

const AGENT_ADDRESS = "a2a-executor-demo";

async function handleIntent(client: AxmeClient, intentId: string) {
  const intentData = await client.getIntent(intentId);
  const intent = intentData.intent ?? intentData;
  let payload = intent.payload ?? {};
  if (payload.parent_payload) {
    payload = payload.parent_payload;
  }

  const taskId = payload.task_id ?? "unknown";
  const taskType = payload.task_type ?? "unknown";
  const sourceAgent = payload.source_agent ?? "unknown";
  const inputData = payload.input_data ?? {};
  const records = inputData.records ?? 0;
  const enrichment = inputData.enrichment ?? "unknown";

  console.log(`  Receiving task from dispatcher (${sourceAgent})...`);
  console.log(`  Task: ${taskId} (${taskType})`);
  await new Promise((r) => setTimeout(r, 1000));

  console.log(`  Enriching ${records} records with geo data...`);
  await new Promise((r) => setTimeout(r, 2000));

  console.log(`  Enrichment complete.`);
  await new Promise((r) => setTimeout(r, 1000));

  const result = {
    action: "complete",
    task_id: taskId,
    records_processed: records,
    enrichment_applied: enrichment,
    success_rate: 0.98,
    executed_at: new Date().toISOString(),
  };

  await client.resumeIntent(intentId, result, { ownerAgent: AGENT_ADDRESS });
  console.log(`  Task ${taskId} completed. ${records} records enriched (${enrichment}).`);
  console.log(`  Result sent back to dispatcher via AXME.`);
}

async function main() {
  const apiKey = process.env.AXME_API_KEY;
  if (!apiKey) {
    console.error("Error: AXME_API_KEY not set.");
    process.exit(1);
  }

  const client = new AxmeClient({ apiKey });

  console.log(`Agent listening on ${AGENT_ADDRESS}...`);
  console.log("Waiting for intents (Ctrl+C to stop)\n");

  for await (const delivery of client.listen(AGENT_ADDRESS)) {
    const intentId = delivery.intent_id;
    const status = delivery.status;

    if (!intentId) continue;

    if (["DELIVERED", "CREATED", "IN_PROGRESS"].includes(status)) {
      console.log(`[${status}] Intent received: ${intentId}`);
      try {
        await handleIntent(client, intentId);
      } catch (e) {
        console.error(`  Error processing intent: ${e}`);
      }
    }
  }
}

main().catch(console.error);
