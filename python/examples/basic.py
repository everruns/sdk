"""Basic example of using the Everruns SDK."""

import asyncio

from everruns_sdk import Everruns


async def main():
    # Initialize client from environment
    client = Everruns()

    try:
        # Create an agent
        agent = await client.agents.create(
            name="Example Assistant",
            system_prompt="You are a helpful assistant for examples.",
        )
        print(f"Created agent: {agent.id}")

        # Create a session
        session = await client.sessions.create(agent_id=agent.id)
        print(f"Created session: {session.id}")

        # Send a message
        message = await client.messages.create(
            session_id=session.id,
            text="Hello, how are you?",
        )
        print(f"Sent message: {message.id}")

        # Stream events
        async for event in client.events.stream(session.id):
            print(f"Event: {event.type}")
            if event.type == "turn.completed":
                break

        # Clean up
        await client.sessions.delete(session.id)
        await client.agents.delete(agent.id)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
