"""Local Tools Example - Everruns SDK.

Demonstrates client-side tool execution: the agent requests a tool call,
the client executes it locally, and sends the result back.

Run: uv run python src/weather_tools.py
Run with verbose: uv run python src/weather_tools.py --verbose
"""

import asyncio
import json
import os
import sys

from everruns_sdk import ContentPart, Everruns, extract_tool_calls
from everruns_sdk.sse import EventStream, StreamOptions

SYSTEM_PROMPT = (
    "You are a helpful weather assistant. You have access to a tool called `get_weather` "
    'that accepts a JSON argument `{"city": "<city name>"}` and returns current weather. '
    "When the user asks about weather, call the tool and then summarize the result."
)

WEATHER_DATA = {
    "paris": (18, "partly cloudy"),
    "tokyo": (22, "sunny"),
    "new york": (15, "rainy"),
}


def get_weather(city: str) -> dict:
    """Simulated local weather lookup."""
    temp, condition = WEATHER_DATA.get(city.lower(), (20, "clear"))
    return {"city": city, "temperature_celsius": temp, "condition": condition}


def handle_tool_call(call_id: str, name: str, arguments: dict) -> ContentPart:
    """Dispatch a tool call by name and return a ContentPart with the result."""
    if name == "get_weather":
        city = arguments.get("city", "unknown")
        result = get_weather(city)
        return ContentPart.make_tool_result(call_id, result)
    return ContentPart.make_tool_error(call_id, f"Unknown tool: {name}")


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


async def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    client = dev_client()

    try:
        # Create agent with tool-aware system prompt
        agent = await client.agents.create(
            name="Weather Assistant",
            system_prompt=SYSTEM_PROMPT,
        )
        print(f"Created agent: {agent.id}")

        # Create session
        session = await client.sessions.create(agent_id=agent.id)
        print(f"Created session: {session.id}\n")

        # Send user message
        await client.messages.create(
            session_id=session.id,
            text="What's the weather like in Paris?",
        )

        # Stream events and handle tool calls
        options = StreamOptions(max_retries=3)
        stream = EventStream(client, session.id, options)
        async for event in stream:
            if verbose:
                print(f"\n[EVENT] {event.type}: {json.dumps(event.data, indent=2)}")

            if event.type == "output.message.completed":
                tool_calls = extract_tool_calls(event.data)
                if tool_calls:
                    print(f"Agent requested {len(tool_calls)} tool call(s)")
                    results = []
                    for tc in tool_calls:
                        print(f"  -> Executing {tc.name}({tc.arguments})")
                        results.append(handle_tool_call(tc.id, tc.name, tc.arguments))

                    # Send tool results back
                    await client.messages.create_tool_results(
                        session_id=session.id,
                        results=results,
                    )
                    print("  <- Sent tool results\n")
                else:
                    text = extract_text(event.data)
                    if text:
                        print(f"Assistant: {text}")

            elif event.type == "turn.completed":
                print("\n[Turn completed]")
                break

            elif event.type == "turn.failed":
                print("\n[Turn failed]")
                break

    finally:
        await client.close()


def dev_client() -> Everruns:
    """Create client configured for local development."""
    api_key = os.environ.get("EVERRUNS_API_KEY")
    if not api_key:
        raise ValueError("EVERRUNS_API_KEY environment variable required")
    base_url = os.environ.get("EVERRUNS_API_URL")
    return Everruns(api_key=api_key, base_url=base_url)


if __name__ == "__main__":
    asyncio.run(main())
