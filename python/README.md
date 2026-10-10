# Everruns SDK for Python

Python SDK for the Everruns API.

## Installation

```bash
pip install everruns-sdk
```

## Call your agent from code

Use `AgentClient` to call one agent from an application. It holds an agent key
(`evr_ak_...`) that reaches that agent's session routes and nothing else.

```python
import asyncio
from everruns_sdk import AgentClient


async def main():
    # EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY, or pass agent_url= and credential=
    agent = AgentClient()

    # One call: create a session, send, wait for the turn, return the reply text
    print(await agent.run("What is the status of order 42?"))

    # Act for one of your application's users (key needs the `end_user` permission)
    alice = agent.for_end_user("customer-42")
    session = await alice.create_session("Order question")
    await alice.send_message(session["id"], "Where is my package?")
    async for event in alice.stream_events(session["id"], after_sequence=0):
        if event.type == "turn.completed":
            break

    # For a browser or mobile app: hand over a short-lived runtime token, never the key
    token = await alice.runtime_token()
    print(token["access_token"], token["expires_in"])

    await agent.close()


asyncio.run(main())
```

The same client works against the Everruns server
(`https://app.everruns.com/api/v1/channels/<channel_id>`) and a serve app.

The management client below (`Everruns`) is for managing Everruns (agents,
harnesses, workspaces) with a personal access token. Calling an agent through its
`sessions.create` / `messages.create` still works but is deprecated and warns once;
use `AgentClient` instead.

## Management Quick Start

```python
import asyncio
from everruns_sdk import Everruns


async def main():
    # Uses EVERRUNS_API_KEY and optional EVERRUNS_ORG_ID environment variables
    client = Everruns()

    # Create an agent
    agent = await client.agents.create(
        name="Assistant",
        system_prompt="You are a helpful assistant.",
    )

    # Create a session
    session = await client.sessions.create(agent_id=agent.id)

    # Send a message
    await client.messages.create(session.id, "Hello!")

    # Stream events
    async for event in client.events.stream(session.id):
        if event.type == "output.message.completed":
            print(event.data)
            break

    await client.close()


asyncio.run(main())
```

## Agent Harness

Each agent owns a harness. Set it on create/update with `harness_name` (preferred) or `harness_id` (mutually exclusive); omit both to default to the org's `generic` harness. A session created from the agent runs on the agent's harness.

```python
# Create an agent on a specific harness
agent = await client.agents.create(
    name="researcher",
    system_prompt="You do deep research.",
    harness_name="deep-research",
)

# Agent-first session: no harness needed — it runs on the agent's harness
session = await client.sessions.create(agent_name="researcher")
```

## Harnesses & Models

Discover and manage harnesses, and browse available models to choose a `default_model_id`.

```python
# Browse harnesses, then create one
harnesses = await client.harnesses.list()  # or .search("research")
harness = await client.harnesses.get(harnesses[0].id)
custom = await client.harnesses.create(
    name="my-harness",
    system_prompt="Base instructions for every session.",
)
examples = await client.harnesses.list_examples()

# List models to pick a default for an agent
models = await client.models.list()
```

## Initial Files

```python
from everruns_sdk import Everruns, InitialFile

client = Everruns()

session = await client.sessions.create(
    agent_id="agent_...",
    initial_files=[
        InitialFile(
            path="/workspace/README.md",
            content="# Demo Project\n",
            encoding="text",
            is_readonly=True,
        ),
        InitialFile(
            path="/workspace/src/app.py",
            content='print("hello")\n',
            encoding="text",
        ),
    ],
)
```

Runnable example: [`examples/initial_files.py`](examples/initial_files.py)

## Authentication

The SDK uses personal access token authentication. Set `EVERRUNS_API_KEY` or pass the token explicitly. For personal access tokens with access to multiple organizations, set `EVERRUNS_ORG_ID` or pass `org_id` explicitly:

```python
# From environment
client = Everruns()
```

Or with an explicit token and organization:

```python
client = Everruns(api_key="evr_pat_...", org_id="org_...")
```

## Change Reasons

Record why a change was made. `with_reason` derives a client that sends the
reason with every request it makes; the server stores it in the changed
entity's history. The derived client shares the original's connection, and the
original stays unchanged:

```python
await client.with_reason("retire the unused agent").agents.delete("agent_123")

scoped = client.with_reason("rotate prompts for the Q3 launch")
await scoped.agents.apply(agent_id, "assistant", "You are concise.")
```

The reason travels in the `Everruns-Change-Reason` header, UTF-8
percent-encoded. A blank reason sends no header. The server trims the reason and rejects it with HTTP 400 (`invalid_change_reason`) when it is longer than 1000 characters, contains control characters other than newline and tab, or looks like it contains a credential. Closing a derived
client is a no-op; close the client it came from.

## Agent Versions

```python
version = await client.agents.create_version(
    "agent_...",
    change_kind="manual",
    summary="Baseline",
)

versions = await client.agents.list_versions("agent_...")
diff = await client.agents.diff_versions("agent_...", "agentver_1", version.id)
fork = await client.agents.fork_version(
    "agent_...",
    version.id,
    name="forked-agent",
)
rollback = await client.agents.rollback_version(
    "agent_...",
    version.id,
    save_version=True,
)
```

## Workspaces

Workspaces hold files shared across sessions.

```python
workspace = await client.workspaces.create(name="team-docs")

await client.workspace_files.create(
    workspace.id,
    "/notes/welcome.md",
    "# Welcome\n",
    encoding="text",
)
file = await client.workspace_files.read(workspace.id, "/notes/welcome.md")
files = await client.workspace_files.list(workspace.id, recursive=True)
```

Runnable example: [`examples/workspaces.py`](examples/workspaces.py)

## Memories

Memories are long-term, searchable knowledge stores for agents.

```python
memory = await client.memories.create(name="product-knowledge")

await client.memories.create_file(
    memory.id,
    "/facts/product.md",
    "# Product\n",
    encoding="text",
)
results = await client.memories.grep_files(memory.id, "product")
await client.memories.sync(memory.id)
```

Runnable example: [`examples/memories.py`](examples/memories.py)

## License

MIT
