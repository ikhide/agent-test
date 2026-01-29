#!/usr/bin/env node

/**
 * MCP Server
 * Exposes snapshot-tool (MCP1) and ocr-extract-tool (MCP2)
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema
} from "@modelcontextprotocol/sdk/types.js";

import { snapshotToolDefinition, snapshotTool } from "./tools/snapshot.js";
import { ocrExtractToolDefinition, ocrExtractTool } from "./tools/ocr-extract.js";

const tools = [snapshotToolDefinition, ocrExtractToolDefinition];

const server = new Server(
  {
    name: "screen-capture-mcp",
    version: "1.0.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      case "snapshot-tool":
        result = await snapshotTool(args.filename);
        break;

      case "ocr-extract-tool":
        result = await ocrExtractTool(args.imagePath, args.outputFilename);
        break;

      default:
        result = { error: `Unknown tool: ${name}` };
    }

    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
    };
  } catch (error) {
    return {
      content: [{ type: "text", text: JSON.stringify({ error: error.message }) }]
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running (snapshot-tool, ocr-extract-tool)");
}

main().catch(console.error);
