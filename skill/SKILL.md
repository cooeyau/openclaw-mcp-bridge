---
name: mcp-bridge
description: Connect to MCP servers (jDocMunch, jCodeMunch, etc.) for structured document and code retrieval. Use when agents need to search or retrieve specific sections from large documentation files or code symbols, instead of reading entire files.
version: 1.0.0
os: linux
---

# MCP Bridge Skill

Connect OpenClaw agents to any MCP server via a CLI bridge.

## When to Use

- Searching large documentation files for specific sections
- Retrieving code symbols (functions, classes) without reading entire files
- Any task where an MCP server provides structured access to data

## Commands

### List configured servers
```bash
mcp-bridge servers
```

### List tools from a server
```bash
mcp-bridge tools <server>
```

### Index a local docs folder (jDocMunch)
```bash
mcp-bridge call jdocmunch index_local --args '{"path": "/path/to/docs"}'
```

### Search for doc sections
```bash
mcp-bridge call jdocmunch search_sections --args '{"repo": "local/myproject", "query": "database schema", "max_results": 5}'
```

### Retrieve a specific section
```bash
mcp-bridge call jdocmunch get_section --args '{"repo": "local/myproject", "section_id": "local/myproject::FILE.md::section-heading#3"}'
```

### Get table of contents
```bash
mcp-bridge call jdocmunch get_toc --args '{"repo": "local/myproject"}'
```

## Workflow Pattern

1. **First time:** Index the docs folder once
2. **Search:** Find the section you need by query
3. **Retrieve:** Get just that section's content
4. **Result:** Exact content, minimal tokens

## Configuration

Servers configured in `~/.config/mcp-bridge/servers.json` or `/root/projects/openclaw-mcp-bridge/servers.json`.

## Notes

- Each `mcp-bridge call` spawns a fresh MCP server process — stateless between calls
- Indexes persist in `~/.doc-index/` (jDocMunch) or `~/.code-index/` (jCodeMunch)
- Re-index after significant doc changes to keep sections current
