# Connect an AG-UI client

Everruns agents speak [AG-UI 1.0](https://docs.ag-ui.com). Any AG-UI client, such as
`@ag-ui/client` or CopilotKit, can talk to an agent through an AG-UI endpoint. You don't need
the Everruns SDK for this: the endpoint is the AG-UI wire protocol, so you use the AG-UI client
directly.

## 1. Create the endpoint

In the Everruns UI, open the agent's **Integrations** tab, add an **AG-UI** endpoint, and
publish it. The endpoint id goes into the URL:

```text
POST https://<your-everruns-host>/v1/e/{endpoint_id}/ag-ui
```

An endpoint is either anonymous or token-protected. A token-protected endpoint takes the token
as `Authorization: Bearer <token>` or as the `x-everruns-ag-ui-token` header.

## 2. Run the agent

```bash
npm install @ag-ui/client
```

```typescript
import { HttpAgent } from "@ag-ui/client";

const agent = new HttpAgent({
  url: `https://<your-everruns-host>/v1/e/${process.env.EVERRUNS_ENDPOINT_ID}/ag-ui`,
  headers: { Authorization: `Bearer ${process.env.EVERRUNS_AG_UI_TOKEN}` },
  threadId: "support-thread-1",
});

agent.addMessage({ id: "m1", role: "user", content: "What changed in my last order?" });

let interrupts = [];
await agent.runAgent({}, {
  onTextMessageContentEvent: ({ event }) => process.stdout.write(event.delta),
  onRunFinishedEvent: ({ event }) => {
    if (event.outcome?.type === "interrupt") interrupts = event.outcome.interrupts;
  },
});
```

The `threadId` picks the conversation: runs with the same thread id continue the same Everruns
session. Each thread is isolated per endpoint, so the same id on two endpoints names two
different sessions.

## 3. Answer interrupts

When the agent stops to ask something, the run ends with `RUN_FINISHED` and
`outcome.type === "interrupt"`. Each interrupt has an `id`, a `reason` and, when the client may
answer it, a `responseSchema` that describes the expected payload.

| `reason` | What it asks | Payload |
|---|---|---|
| `everruns.ask_user` | The agent's `ask_user` questions | `{ "answers": [{ "id": "...", "selected": ["..."] }] }` |
| `tool_approval` | Approval to run a tool, on endpoints that allow client approvals | `{ "decision": "allow" }` (or `allow_always`, `reject`, `reject_always`) |
| `everruns.operator_approval` | A tool approval that only an operator can give | none: wait, or abandon it |
| `everruns.secret_required` | A credential, which is never sent over AG-UI | none: abandon it |

The next run on the same thread carries the answers in `resume` and needs no new user message:

```typescript
await agent.runAgent({
  resume: interrupts.map((interrupt) => ({
    interruptId: interrupt.id,
    status: "resolved",
    payload: { answers: [{ id: "target", selected: ["Staging"] }] },
  })),
});
```

Every open interrupt needs an entry. To decline one, send `status: "cancelled"`. A run that
leaves an interrupt out resolves nothing and ends with the same interrupts again.

## 4. Frontend tools

Tools passed to the run are executed by your client. When the agent calls one, the run streams
`TOOL_CALL_START`, `TOOL_CALL_ARGS` and `TOOL_CALL_END`, and finishes in success with
`pendingToolCallIds`. Send the results as `tool` messages in the next run:

```typescript
const tools = [{
  name: "set_theme",
  description: "Switch the page theme.",
  parameters: { type: "object", properties: { theme: { type: "string" } } },
}];

await agent.runAgent({ tools });
// ...run the call, then:
agent.addMessage({ id: "t1", role: "tool", toolCallId: callId, content: '{"applied":true}' });
await agent.runAgent({ tools });
```

CopilotKit does this for you with `useFrontendTool`.

## Token usage

Endpoints with usage reporting turned on add `usage` to `RUN_FINISHED`: one entry per provider
and model, where `inputTokens` includes cached input.
