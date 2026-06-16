# Getting Started

## Installation

### Rust

```toml
[dependencies]
everruns-sdk = "0.1"
```

### Python

```bash
pip install everruns-sdk
```

### TypeScript

```bash
npm install @everruns/sdk
```

## Quick Start

### 1. Set Personal Access Token

```bash
export EVERRUNS_API_KEY=evr_pat_...
# Optional for personal access tokens with access to multiple organizations:
export EVERRUNS_ORG_ID=org_...
```

### 2. Create Client

```python
from everruns_sdk import Everruns

client = Everruns()
```

### 3. Create an Agent

```python
agent = client.agents.create(
    name="Assistant",
    system_prompt="You are a helpful assistant."
)
```

### 4. Start a Session

```python
session = client.sessions.create(agent_id=agent.id)
```

### 4a. Start a Session with Initial Files

```python
from everruns_sdk import InitialFile

session = client.sessions.create(
    agent_id=agent.id,
    initial_files=[
        InitialFile(
            path="/workspace/README.md",
            content="# Demo Project\n",
            encoding="text",
            is_readonly=True,
        )
    ],
)
```

### 5. Send a Message

```python
client.messages.create(session.id, text="Hello!")
```

### 6. Stream Events

```python
async for event in client.events.stream(session.id):
    if event.type == "output.message.completed":
        print(event.data.message.content)
```

### 7. Workspaces

Workspaces hold files shared across sessions.

```python
workspace = await client.workspaces.create(name="team-docs")

await client.workspace_files.create(
    workspace.id,
    "/notes/welcome.md",
    "# Welcome\n",
    encoding="text",
)
files = await client.workspace_files.list(workspace.id, recursive=True)
```

### 8. Memories

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
```

## Next Steps

- See `cookbook/` for practical recipes
- See `specs/` for detailed specifications
