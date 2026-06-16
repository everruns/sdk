"""Example: create a workspace and manage its files.

Run with:
    EVERRUNS_API_KEY=evr_... uv run python examples/workspaces.py
"""

import asyncio

from everruns_sdk import Everruns


async def main():
    client = Everruns()

    try:
        workspace = await client.workspaces.create(
            name="workspaces-example-py",
            description="Shared files for the team",
        )
        print(f"Created workspace {workspace.id}")

        await client.workspace_files.create(
            workspace.id,
            "/notes/welcome.md",
            "# Welcome\n\nShared workspace files live here.\n",
            encoding="text",
        )

        file = await client.workspace_files.read(workspace.id, "/notes/welcome.md")
        print(f"Read {file.path}:")
        print(file.content)

        files = await client.workspace_files.list(workspace.id, recursive=True)
        print(f"Workspace has {len(files)} file(s)")

        await client.workspaces.delete(workspace.id)
        print("Archived workspace")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
