#!/usr/bin/env python3
"""MongoDB MCP helper — wraps connect + query in a single session."""

import asyncio
import json
import sys
import os

from contextlib import AsyncExitStack
from datetime import timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CONNECTION_STRING = os.environ.get(
    "MDB_MCP_CONNECTION_STRING",
    "mongodb://localhost:27017"
)

async def run(tool_name: str, args: dict):
    params = StdioServerParameters(
        command="npx",
        args=["-y", "mongodb-mcp-server"],
        env={**os.environ},
    )
    
    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(
            ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30))
        )
        await session.initialize()
        
        # Connect first
        connect_result = await session.call_tool("connect", arguments={
            "connectionString": CONNECTION_STRING
        })
        
        # Now run the actual query
        result = await session.call_tool(tool_name, arguments=args)
        
        for content in result.content:
            if hasattr(content, "text"):
                print(content.text)
        
        if result.isError:
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: mcp-mongodb <tool> [--args '{...}']")
        print("Tools: list-databases, list-collections, find, aggregate, count, collection-schema, etc.")
        sys.exit(1)
    
    tool = sys.argv[1]
    args = {}
    if "--args" in sys.argv:
        idx = sys.argv.index("--args")
        args = json.loads(sys.argv[idx + 1])
    
    try:
        asyncio.run(run(tool, args))
    except (ExceptionGroup, BaseExceptionGroup):
        pass  # Suppress MCP session cleanup noise
