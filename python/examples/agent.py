"""Call an agent from code with an agent key.

Run against a real agent API channel:

    export EVERRUNS_AGENT_URL=https://app.everruns.com/api/v1/channels/<channel_id>
    export EVERRUNS_AGENT_KEY=evr_ak_...
    uv run python examples/agent.py "What can you do?"
"""

import asyncio
import sys

from everruns_sdk import AgentClient


async def main() -> None:
    question = " ".join(sys.argv[1:]) or "Hello! What can you do?"
    async with AgentClient() as agent:
        card = await agent.card()
        print(f"Agent: {card['name']}")
        print(await agent.run(question))


if __name__ == "__main__":
    asyncio.run(main())
