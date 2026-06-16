# Everruns SDK for Python

Python SDK for the Everruns API.

## Installation

```bash
pip install everruns-sdk
```

## Quick Start

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

# Explicit token and organization
client = Everruns(api_key="evr_pat_...", org_id="org_...")
```

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
