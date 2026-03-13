#!/usr/bin/env python3
"""
openclaw-mcp-bridge — MCP Client Bridge for OpenClaw Agents

Spawns MCP servers as child processes and lets OpenClaw agents call their
tools via a simple CLI interface. Bridges the gap until OpenClaw ships
native MCP client support.

Usage:
  mcp-bridge tools <server>                          # List available tools
  mcp-bridge call <server> <tool> [--args '{}']      # Call a tool
  mcp-bridge resources <server>                      # List available resources
  mcp-bridge resource <server> <uri>                 # Read a resource
  mcp-bridge servers                                 # List configured servers

Config: ~/.config/mcp-bridge/servers.json
"""

import asyncio
import json
import sys
import os
import argparse
from pathlib import Path
from contextlib import AsyncExitStack

from datetime import timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Timeout for MCP server responses (handles slow starters like MongoDB)
READ_TIMEOUT = timedelta(seconds=30)

# Config locations (in priority order)
CONFIG_PATHS = [
    Path(os.environ.get("MCP_BRIDGE_CONFIG", "")),
    Path.home() / ".config" / "mcp-bridge" / "servers.json",
    Path("/root/projects/openclaw-mcp-bridge/servers.json"),
]

DEFAULT_TIMEOUT = 30  # seconds


def load_config() -> dict:
    """Load server configuration."""
    for path in CONFIG_PATHS:
        if path and path.is_file():
            with open(path) as f:
                return json.load(f)
    return {"servers": {}}


def get_server_params(config: dict, server_name: str) -> StdioServerParameters:
    """Get StdioServerParameters for a named server."""
    servers = config.get("servers", {})
    if server_name not in servers:
        available = ", ".join(servers.keys()) or "(none configured)"
        print(f"Error: Unknown server '{server_name}'. Available: {available}", file=sys.stderr)
        sys.exit(1)

    srv = servers[server_name]
    return StdioServerParameters(
        command=srv["command"],
        args=srv.get("args", []),
        env={**os.environ, **srv.get("env", {})},
    )


async def run_tools(server_name: str, config: dict):
    """List tools available from an MCP server."""
    params = get_server_params(config, server_name)

    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write, read_timeout_seconds=READ_TIMEOUT))
        await session.initialize()

        result = await session.list_tools()
        tools = result.tools

        if not tools:
            print(f"No tools available from '{server_name}'")
            return

        print(f"Tools from '{server_name}' ({len(tools)}):\n")
        for tool in tools:
            print(f"  {tool.name}")
            if tool.description:
                desc = tool.description[:120]
                print(f"    {desc}")
            if tool.inputSchema and tool.inputSchema.get("properties"):
                props = tool.inputSchema["properties"]
                params_str = ", ".join(
                    f"{k}: {v.get('type', '?')}" for k, v in props.items()
                )
                print(f"    params: {params_str}")
            print()


async def run_call(server_name: str, tool_name: str, args: dict, config: dict):
    """Call a tool on an MCP server and return the result."""
    params = get_server_params(config, server_name)

    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write, read_timeout_seconds=READ_TIMEOUT))
        await session.initialize()

        result = await session.call_tool(tool_name, arguments=args)

        # Extract content
        for content in result.content:
            if hasattr(content, "text"):
                print(content.text)
            elif hasattr(content, "data"):
                print(json.dumps({"type": "binary", "mimeType": getattr(content, "mimeType", "unknown")}))
            else:
                print(json.dumps(content.model_dump() if hasattr(content, "model_dump") else str(content)))

        if result.isError:
            sys.exit(1)


async def run_resources(server_name: str, config: dict):
    """List resources available from an MCP server."""
    params = get_server_params(config, server_name)

    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write, read_timeout_seconds=READ_TIMEOUT))
        await session.initialize()

        result = await session.list_resources()
        resources = result.resources

        if not resources:
            print(f"No resources available from '{server_name}'")
            return

        print(f"Resources from '{server_name}' ({len(resources)}):\n")
        for res in resources:
            print(f"  {res.uri}")
            if res.name:
                print(f"    name: {res.name}")
            if res.description:
                print(f"    desc: {res.description[:100]}")
            print()


async def run_resource(server_name: str, uri: str, config: dict):
    """Read a specific resource from an MCP server."""
    params = get_server_params(config, server_name)

    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write, read_timeout_seconds=READ_TIMEOUT))
        await session.initialize()

        result = await session.read_resource(uri)
        for content in result.contents:
            if hasattr(content, "text"):
                print(content.text)
            else:
                print(json.dumps(content.model_dump() if hasattr(content, "model_dump") else str(content)))


def list_servers(config: dict):
    """List configured MCP servers."""
    servers = config.get("servers", {})
    if not servers:
        print("No servers configured.")
        print(f"Add servers to: {CONFIG_PATHS[1]}")
        return

    print(f"Configured MCP servers ({len(servers)}):\n")
    for name, srv in servers.items():
        cmd = f"{srv['command']} {' '.join(srv.get('args', []))}"
        desc = srv.get("description", "")
        print(f"  {name}")
        print(f"    command: {cmd}")
        if desc:
            print(f"    desc: {desc}")
        print()


def main():
    parser = argparse.ArgumentParser(
        prog="mcp-bridge",
        description="MCP Client Bridge for OpenClaw — connect agents to MCP servers",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # servers
    subparsers.add_parser("servers", help="List configured MCP servers")

    # tools
    p_tools = subparsers.add_parser("tools", help="List tools from an MCP server")
    p_tools.add_argument("server", help="Server name from config")

    # call
    p_call = subparsers.add_parser("call", help="Call a tool on an MCP server")
    p_call.add_argument("server", help="Server name from config")
    p_call.add_argument("tool", help="Tool name to call")
    p_call.add_argument("--args", "-a", default="{}", help="JSON arguments for the tool")

    # resources
    p_res = subparsers.add_parser("resources", help="List resources from an MCP server")
    p_res.add_argument("server", help="Server name from config")

    # resource
    p_read = subparsers.add_parser("resource", help="Read a resource from an MCP server")
    p_read.add_argument("server", help="Server name from config")
    p_read.add_argument("uri", help="Resource URI to read")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_config()

    if args.command == "servers":
        list_servers(config)
    elif args.command == "tools":
        asyncio.run(run_tools(args.server, config))
    elif args.command == "call":
        tool_args = json.loads(args.args)
        asyncio.run(run_call(args.server, args.tool, tool_args, config))
    elif args.command == "resources":
        asyncio.run(run_resources(args.server, config))
    elif args.command == "resource":
        asyncio.run(run_resource(args.server, args.uri, config))


if __name__ == "__main__":
    main()
