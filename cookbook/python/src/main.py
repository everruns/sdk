"""Dad Jokes Agent - Everruns SDK Example.

Run: uv run python src/main.py
Run with verbose: uv run python src/main.py --verbose
"""

import asyncio
import json
import os
import sys

from everruns_sdk import Everruns


async def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    client = dev_client()

    try:
        # Create agent
        agent = await client.agents.create(
            name="Dad Jokes Bot",
            system_prompt="You are a dad joke expert. Tell one short, cheesy dad joke.",
        )
        print(f"Created agent: {agent.id}")

        # Create session
        session = await client.sessions.create(agent_id=agent.id)
        print(f"Created session: {session.id}\n")

        # Send message
        await client.messages.create(
            session_id=session.id,
            text="Tell me a dad joke",
        )

        # Stream events
        async for event in client.events.stream(session.id):
            if verbose:
                print(f"\n[EVENT] {event.type}: {json.dumps(event.data, indent=2)}")

            if event.type == "input.message":
                text = extract_text(event.data)
                if text:
                    print(f"Input: {text}")
                else:
                    print(f"Input (raw): {json.dumps(event.data, indent=2)}")

            elif event.type == "output.message.completed":
                text = extract_text(event.data)
                if text:
                    print(f"Output: {text}")
                else:
                    print(f"Output (raw): {json.dumps(event.data, indent=2)}")

            elif event.type == "turn.completed":
                print("\n[Turn completed]")
                break

            elif event.type == "turn.failed":
                print("\n[Turn failed]")
                break

    finally:
        await client.close()


def extract_text(data: dict) -> str | None:
    """Extract text content from message event data."""
    message = data.get("message")
    if not message:
        return None

    content = message.get("content")
    if not content or not isinstance(content, list):
        return None

    texts = []
    for part in content:
        if isinstance(part, dict) and part.get("type") == "text":
            text = part.get("text")
            if text:
                texts.append(text)

    return "".join(texts) if texts else None


def dev_client() -> Everruns:
    """Create client configured for local development."""
    api_key = os.environ.get("EVERRUNS_API_KEY")
    if not api_key:
        raise ValueError("EVERRUNS_API_KEY environment variable required")

    base_url = os.environ.get("EVERRUNS_API_URL")

    return Everruns(api_key=api_key, base_url=base_url)


if __name__ == "__main__":
    asyncio.run(main())
