/**
 * Example: create a workspace and manage its files.
 *
 * Run with:
 * `EVERRUNS_API_KEY=evr_... npx tsx examples/workspaces.ts`
 */

import { Everruns } from "../src/index.js";

async function main() {
  const client = Everruns.fromEnv();

  const workspace = await client.workspaces.create({
    name: "workspaces-example-ts",
    description: "Shared files for the team",
  });
  console.log("Created workspace", workspace.id);

  await client.workspaceFiles.create(
    workspace.id,
    "/notes/welcome.md",
    "# Welcome\n\nShared workspace files live here.\n",
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

  await client.workspaces.delete(workspace.id);
  console.log("Archived workspace");
}

main().catch(console.error);
