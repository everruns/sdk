# Everruns SDK Cookbook

Runnable examples for each SDK.

## Server Setup

```bash
cargo install --git https://github.com/everruns/everruns everruns-server
export DEFAULT_ANTHROPIC_API_KEY=sk-ant-...  # or DEFAULT_OPENAI_API_KEY
DEV_MODE=1 everruns-server
```

## Cookbooks

- [rust/](rust/) - Rust SDK example
- [python/](python/) - Python SDK example
- [typescript/](typescript/) - TypeScript SDK example

## Workspaces & Memories

Workspaces hold files shared across sessions; memories are long-term,
searchable knowledge stores for agents. Runnable, single-file examples live in
each SDK's `examples/` directory:

| SDK | Workspaces | Memories |
|---|---|---|
| Rust | `cargo run --example workspaces` | `cargo run --example memories` |
| Python | `uv run python examples/workspaces.py` | `uv run python examples/memories.py` |
| TypeScript | `npx tsx examples/workspaces.ts` | `npx tsx examples/memories.ts` |
