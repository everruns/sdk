"""Agent client - call one agent from code with an agent key.

Create an Agent API channel, publish it, and create an agent key (see
docs/features/channels.md), then:

    export EVERRUNS_AGENT_URL=http://localhost:9000/api/v1/channels/<channel_id>
    export EVERRUNS_AGENT_KEY=evr_ak_...
    uv run python src/agent_client.py
"""

import asyncio

from everruns_sdk import AgentClient


async def main():
    async with AgentClient() as agent:
        card = await agent.card()
        print(f"Agent: {card['name']}")

        # One call: session, message, wait for the turn, final text
        print(await agent.run("Tell me a dad joke"))

        # Follow-up in the same session, following the stream yourself
        session = await agent.create_session("Follow-up")
        await agent.send_message(session["id"], "Tell me another")
        async for event in agent.stream_events(session["id"], after_sequence=0):
            if event.type == "output.message.completed":
                print(event.data)
            if event.type in ("turn.completed", "turn.failed"):
                break


if __name__ == "__main__":
    asyncio.run(main())
