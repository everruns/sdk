# Agent Client Specification

Language-agnostic requirements for the agent client: the SDK surface for calling
one agent from code through the Agent Execution API. Upstream contract:
`knowledge/integrations/agent-execution-api.md` and
`crates/contracts/src/execution_api.rs` in everruns/everruns; public docs in
`docs/features/channels.md` ("Agent API").

## Why a separate client

The management client (`Everruns`) holds a personal access token and reaches
every management route of an organization. The agent client holds a credential
that reaches one agent's session routes and nothing else (an agent key
`evr_ak_…`, a runtime token, an identity-provider token, or a member's personal
access token when the agent allows it). It is the recommended way to call an
agent from an application. The management client is deprecated for that use.

The same routes and shapes are served by the everruns server
(`{api}/v1/channels/{channel_id}`) and by a serve app
(`{host}/v1/channels/{agent}`), so one client works against both.

## Initialization

| Parameter | Env variable | Description |
|---|---|---|
| `agent_url` | `EVERRUNS_AGENT_URL` | Agent base URL, e.g. `https://app.everruns.com/api/v1/channels/apichan_…` |
| `credential` | `EVERRUNS_AGENT_KEY` | Bearer credential: agent key, runtime token, or IdP/PAT token |
| `end_user` | (none) | Optional. Sent as `End-User` on every request (needs a key holding `end_user`) |

```
agent = AgentClient()                             # from env
agent = AgentClient(agent_url=..., credential="evr_ak_...")
alice = agent.for_end_user("customer-42")         # derived client, same pool
```

`for_end_user` returns a derived client like `with_reason` on the management
client: same configuration and connection pool, `End-User` set. Names per
language: Rust `AgentClient::for_end_user`, Python `AgentClient.for_end_user`,
TypeScript `agent.forEndUser`. The type is `AgentClient` in all three
(Rust `everruns_sdk::AgentClient`, Python `everruns_sdk.AgentClient`, TypeScript
`AgentClient`). Not `Agent`: that name is the management model type.

Missing URL or credential is a configuration error at construction, as for the
management client. The URL has any trailing slash removed.

## Operations

All paths are relative to the agent base URL. JSON bodies; errors use the SDK's
existing error types (status, message, problem `code` when present).

| Method (snake / camel) | HTTP | Notes |
|---|---|---|
| `card` | `GET /` (the base URL itself) | Returns the agent card |
| `create_session(title?, idempotency_key?)` / `createSession` | `POST /sessions` | Body `{}` or `{"title": ...}`; 201 |
| `list_sessions(limit?, page_token?)` / `listSessions` | `GET /sessions` | `{data, next_page_token?}` |
| `get_session(session_id)` / `getSession` | `GET /sessions/{id}` | Includes `pending_questions`, `pending_approvals` |
| `send_message(session_id, text, idempotency_key?)` / `sendMessage` | `POST /sessions/{id}/messages` | Body `{"message": {"role": "user", "content": [{"type": "text", "text": ...}]}}`; 201 |
| `cancel(session_id)` | `POST /sessions/{id}/cancel` | |
| `list_events(session_id, after_sequence?, limit?)` / `listEvents` | `GET /sessions/{id}/events` | `{data}`; page forward with `after_sequence` (exclusive) |
| `stream_events(session_id, since_id?, after_sequence?)` / `streamEvents` | `GET /sessions/{id}/sse` | Reuse the SDK's SSE reader and reconnect rules (`specs/sse-streaming.md`) |
| `answer_questions(session_id, answers)` / `answerQuestions` | `POST /sessions/{id}/question-answers` | Pass-through JSON body |
| `submit_tool_approvals(session_id, decisions)` / `submitToolApprovals` | `POST /sessions/{id}/tool-approvals` | Pass-through JSON body |
| `runtime_token()` / `runtimeToken` | `POST /runtime-auth` | Needs `End-User` (use a `for_end_user` client); returns `{access_token, token_type, expires_in, virtual_user_id}` for a browser |

Plus one convenience: `run(text, session_id?) -> final assistant text`
(`run` in all three). It creates a session when none is given, sends the message,
follows the stream until the turn completes (`turn.completed`) or fails
(`turn.failed`, raised as an error), and returns the last assistant message
text. This is the "call your agent from code" one-liner. On an existing
session, `run` first pages `list_events` to find the newest sequence, sends,
then streams with `after_sequence` set to it, so earlier turns are not replayed;
a new session streams from `after_sequence=0`. A stream that ends before the
turn does is an error.

## Headers

- `Authorization: Bearer <credential>` on every request.
- `End-User: <id>` when the client is a `for_end_user` client.
- `Idempotency-Key: <key>` on `create_session` and `send_message` when the
  caller passes one. Safe retries: a retry with the same key and body returns the
  first response (server sets `Idempotent-Replayed: true`).
- No `X-Org-Id`, no `Everruns-Change-Reason`: the agent URL already names the
  agent and its organization.

## Types

Model the agent card (`name`, `description?`, `streaming`, `input {text, images,
files}`, `auth[] {type, issuer?}`, `conversation_starters[]`, `links`) and the
agent session view (`id`, `title?`, `status`, `created_at`, `updated_at`,
`pending_questions?`, `pending_approvals?`; tolerate unknown fields). Events
reuse the SDK's existing `Event` type. Prefer loose typing (dict / `serde_json::Value`
/ `unknown`) over inventing fields the server does not send.

## Deprecation of the management client for agent calls

The management client keeps working. Its docs (README, docstrings) say: to call an
agent from an application, use `AgentClient` with an agent key; the management
client is for managing Everruns (agents, harnesses, workspaces) with a personal
access token. Python warns once with `DeprecationWarning` when the management
client's `sessions.create` / `messages.create` are used; TypeScript marks them
`@deprecated` in JSDoc; Rust adds a doc note (no `#[deprecated]`, which would
break `-D warnings` builds of existing users).

## Testing

Unit tests against a mock HTTP server (the SDK's existing test approach) cover:
auth header, `End-User` on a derived client, `Idempotency-Key` pass-through,
URL joining (base URL with and without trailing slash, the card at the base URL
itself), error mapping (401, 403, 404, 422 with `code`, 429), and `run` returning
the final text from a scripted SSE stream, raising on `turn.failed`.
