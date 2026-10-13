/**
 * Example: use a session's workspace and manage its files.
 *
 * Every session owns a workspace; there is no standalone workspace creation.
 *
 * Run with:
 * `EVERRUNS_API_KEY=evr_... npx tsx examples/workspaces.ts`
 */

import { Everruns } from "../src/index.js";

async function main() {
  const client = Everruns.fromEnv();

  const session = await client.sessions.create();
  if (!session.workspace_id) {
    throw new Error("session did not expose a workspace_id");
  }
  const workspace = await client.workspaces.get(session.workspace_id);
  console.log(`Session ${session.id} uses workspace ${workspace.id}`);

  await client.workspaceFiles.create(
    workspace.id,
    "/notes/welcome.md",
    "# Welcome\n\nWorkspace files live here.\n",
    { encoding: "text" },
  );

  const file = await client.workspaceFiles.read(
    workspace.id,
    "/notes/welcome.md",
  );
  console.log(`Read ${file.path}:`);
  console.log(file.content);

  const files = await client.workspaceFiles.list(workspace.id, {
    recursive: true,
  });
  console.log(`Workspace has ${files.data.length} file(s)`);

  await client.sessions.delete(session.id);
  console.log("Deleted session");
}

main().catch(console.error);
