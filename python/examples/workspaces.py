"""Example: use a session's workspace and manage its files.

Every session owns a workspace; there is no standalone workspace creation.

Run with:
    EVERRUNS_API_KEY=evr_... uv run python examples/workspaces.py
"""

import asyncio

from everruns_sdk import Everruns


async def main():
    client = Everruns()

    try:
        session = await client.sessions.create()
        workspace = await client.workspaces.get(session.workspace_id)
        print(f"Session {session.id} uses workspace {workspace.id}")

        await client.workspace_files.create(
            workspace.id,
            "/notes/welcome.md",
            "# Welcome\n\nWorkspace files live here.\n",
            encoding="text",
        )

        file = await client.workspace_files.read(workspace.id, "/notes/welcome.md")
        print(f"Read {file.path}:")
        print(file.content)

        files = await client.workspace_files.list(workspace.id, recursive=True)
        print(f"Workspace has {len(files)} file(s)")

        await client.sessions.delete(session.id)
        print("Deleted session")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
