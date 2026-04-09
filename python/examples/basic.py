"""Basic example of using the Everruns SDK."""

import asyncio

from everruns_sdk import AgentCapabilityConfig, Everruns


async def main():
    # Initialize client from environment
    client = Everruns()

    try:
        # Create an agent with current_time capability
        agent = await client.agents.create(
            name="example-assistant",
            system_prompt="You are a helpful assistant for examples.",
            capabilities=[AgentCapabilityConfig(ref="current_time")],
        )
        print("Created agent:")
        print(f"  Name: {agent.name}")
        print(f"  ID: {agent.id}")
        print(f"  Status: {agent.status}")
        print(f"  Capabilities: {agent.capabilities}")
        print(f"  Created: {agent.created_at}")

        # Create a session (agent is optional)
        session = await client.sessions.create(
            agent_id=agent.id,
            capabilities=[AgentCapabilityConfig(ref="current_time")],
        )
        print("Created session:")
        print(f"  ID: {session.id}")
        print(f"  Harness: {session.harness_id}")
        print(f"  Agent: {session.agent_id}")
        print(f"  Status: {session.status}")
        print(f"  Created: {session.created_at}")

        # Send a message that uses the current_time capability
        message = await client.messages.create(
            session_id=session.id,
            text="What time is it right now? Generate a short joke about the current time.",
        )
        print(f"Sent message: {message.id}")

        # Stream events
        async for event in client.events.stream(session.id):
            print(f"Event: {event.type}")
            if event.type in {"output.message.completed", "turn.completed", "turn.failed"}:
                break

        # Clean up
        await client.sessions.delete(session.id)
        await client.agents.delete(agent.id)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
