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

### 1. Set API Key

```bash
export EVERRUNS_API_KEY=evr_...
```

### 2. Create Client

```python
from everruns_sdk import Everruns

client = Everruns(org="my-org")
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

## Next Steps

- See `cookbook/` for practical recipes
- See `specs/` for detailed specifications
