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
    # Uses EVERRUNS_API_KEY environment variable
    client = Everruns(org="my-org")
    
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

## License

MIT
