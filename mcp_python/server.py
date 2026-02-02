#!/usr/bin/env python3
"""
MCP Server
Exposes snapshot-tool (MCP1) and ocr-extract-tool (MCP2)
"""

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.snapshot import snapshot_tool_definition, snapshot_tool
from tools.ocr_extract import ocr_extract_tool_definition, ocr_extract_tool

server = Server("screen-capture-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [snapshot_tool_definition, ocr_extract_tool_definition]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "snapshot-tool":
            result = await snapshot_tool(arguments.get("filename"))
        elif name == "ocr-extract-tool":
            result = await ocr_extract_tool(
                arguments.get("imagePath"),
                arguments.get("outputFilename", "text.txt")
            )
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Run the MCP server."""
    print("MCP Server running (snapshot-tool, ocr-extract-tool)", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
