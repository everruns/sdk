"""Example: create a memory, add files, and search them.

Run with:
    EVERRUNS_API_KEY=evr_... uv run python examples/memories.py
"""

import asyncio

from everruns_sdk import Everruns


async def main():
    client = Everruns()

    try:
        memory = await client.memories.create(
            name="memories-example-py",
            description="Long-term knowledge for the agent",
        )
        print(f"Created memory {memory.id}")

        await client.memories.create_file(
            memory.id,
            "/facts/product.md",
            "# Product\n\nEverruns runs autonomous agents.\n",
            encoding="text",
        )

        results = await client.memories.grep_files(memory.id, "agents")
        print(f"Found {len(results)} match(es) for 'agents'")

        files = await client.memories.list_files(memory.id)
        print(f"Memory has {len(files)} file(s)")

        await client.memories.delete(memory.id)
        print("Archived memory")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
