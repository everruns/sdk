"""Example: create a session with initial files.

Run with:
    EVERRUNS_API_KEY=evr_... uv run python examples/initial_files.py
"""

import asyncio

from everruns_sdk import Everruns, InitialFile


async def main():
    client = Everruns()

    try:
        agent = await client.agents.create(
            name="initial-files-example",
            system_prompt=("You are a helpful assistant. Read the starter files before answering."),
        )

        session = await client.sessions.create(
            agent_id=agent.id,
            title="Session with starter files",
            initial_files=[
                InitialFile(
                    path="/workspace/README.md",
                    content="# Demo Project\n\nThis workspace contains starter files.\n",
                    encoding="text",
                    is_readonly=True,
                ),
                InitialFile(
                    path="/workspace/src/app.py",
                    content='def greet(name: str) -> str:\n    return f"hello, {name}"\n',
                    encoding="text",
                ),
            ],
        )

        print(f"Created session {session.id}")
        print("Starter files:")
        print("  - /workspace/README.md")
        print("  - /workspace/src/app.py")

        message = await client.messages.create(
            session_id=session.id,
            text="Summarize the project and suggest one improvement to src/app.py.",
        )
        print(f"Created message {message.id}")

        await client.sessions.delete(session.id)
        await client.agents.delete(agent.id)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
