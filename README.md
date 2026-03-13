# 🦞 openclaw-mcp-bridge

**MCP Client Bridge for OpenClaw** — Connect your OpenClaw agents to any MCP server.

OpenClaw agents can't natively connect to MCP servers (yet — see [#4834](https://github.com/openclaw/openclaw/issues/4834)). This bridge fills the gap: spawn MCP servers as child processes and call their tools via a simple CLI that agents use through `exec`.

## Why?

MCP (Model Context Protocol) is the standard for connecting AI agents to external tools. Hundreds of MCP servers exist for databases, docs, code, APIs, and more — but OpenClaw agents can't use them.

This bridge changes that. One CLI, any MCP server.

```
OpenClaw Agent → exec → mcp-bridge → MCP Server → structured data back
```

## Quick Start

```bash
# Install
pip install jdocmunch-mcp  # or any MCP server you want
git clone https://github.com/cooeyau/openclaw-mcp-bridge.git
cd openclaw-mcp-bridge
ln -s $(pwd)/src/mcp_bridge.py /usr/local/bin/mcp-bridge

# Configure servers
cp servers.json ~/.config/mcp-bridge/servers.json
# Edit to add your MCP servers

# Use
mcp-bridge servers                    # List configured servers
mcp-bridge tools jdocmunch            # List tools from a server
mcp-bridge call jdocmunch search_sections --args '{"repo": "local/myproject", "query": "authentication"}'
```

## Token Savings Example

**Without bridge** (brute-force file read):
```
Agent reads entire COOEY.md → 82,783 chars → ~20,000 tokens
```

**With bridge** (structured retrieval):
```
mcp-bridge call jdocmunch search_sections → find section → get_section
Result: ~2,000 tokens for exactly the section needed
```

**90% token reduction** on doc lookups.

## Supported MCP Servers

Any MCP server that uses stdio transport works. Tested with:

| Server | Purpose | Install |
|---|---|---|
| [jDocMunch](https://github.com/jgravelle/jdocmunch-mcp) | Document section retrieval | `pip install jdocmunch-mcp` |
| [jCodeMunch](https://github.com/jgravelle/jcodemunch-mcp) | Code symbol retrieval | `pip install jcodemunch-mcp` |

## Configuration

Create `~/.config/mcp-bridge/servers.json`:

```json
{
  "servers": {
    "jdocmunch": {
      "description": "Document section retrieval",
      "command": "jdocmunch-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

## Commands

| Command | Description |
|---|---|
| `mcp-bridge servers` | List configured MCP servers |
| `mcp-bridge tools <server>` | List available tools from a server |
| `mcp-bridge call <server> <tool> --args '{}'` | Call a tool with JSON arguments |
| `mcp-bridge resources <server>` | List available resources |
| `mcp-bridge resource <server> <uri>` | Read a specific resource |

## OpenClaw Skill

An OpenClaw skill is included for teaching agents how to use the bridge. Install it:

```bash
cp -r skill/ ~/.openclaw/skills/mcp-bridge/
```

## How It Works

1. Agent calls `mcp-bridge` via `exec`
2. Bridge spawns the MCP server as a child process (stdio transport)
3. Performs MCP handshake (`initialize` → `initialized`)
4. Routes the tool call via JSON-RPC 2.0
5. Returns the result to stdout
6. Server process exits cleanly

No daemons, no ports, no config servers. Just a CLI wrapper around the MCP protocol.

## Requirements

- Python 3.10+
- `mcp` Python SDK (`pip install mcp`)
- Any MCP server you want to connect to

## License

MIT

## Credits

- Built by [Cooey](https://cooey.au) for the [OpenClaw](https://github.com/openclaw/openclaw) community
- Inspired by [openclaw-mcp](https://github.com/freema/openclaw-mcp) by Tomáš Grasl — an MCP server that exposes OpenClaw to Claude.ai. We built the reverse: an MCP client that gives OpenClaw agents access to MCP servers.
- Powered by Anthropic's [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [jDocMunch](https://github.com/jgravelle/jdocmunch-mcp) and [jCodeMunch](https://github.com/jgravelle/jcodemunch-mcp) by J. Gravelle for document and code retrieval
