# Copilot Agent Orchestrator

Multi-agent orchestration system with MCP tools for GitHub Copilot.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Copilot                        │
│             @testOrc run screen process                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           Orchestrator (Routes Commands)                 │
│                                                          │
│   "run screen process" → Screen Agent                    │
│   "run <command>"      → Appropriate Agent               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    Agents Layer                          │
├─────────────────────────────────────────────────────────┤
│  Screen Agent        │  (Future Agents)                  │
│  - snapshot-tool     │  - data-agent                     │
│  - ocr-extract-tool  │  - review-agent                   │
└──────────────────────┴──────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    MCP Tools                             │
├─────────────────────┬───────────────────────────────────┤
│  MCP1: snapshot     │  MCP2: ocr-extract                 │
│  Takes screenshot   │  Extracts text via Tesseract       │
│  Saves to snapshots/│  Saves to output/text.txt          │
└─────────────────────┴───────────────────────────────────┘
```

## Quick Start

```bash
# Install dependencies
npm install

# Start the orchestrator server
npm start
```

## Components

### MCP Tools (`mcp/`)

1. **snapshot-tool** - Takes a screenshot and saves to `snapshots/`
2. **ocr-extract-tool** - Extracts text from image using Tesseract.js, saves to `output/text.txt`

### Agents (`agents/`)

1. **screen-agent** - Coordinates snapshot → OCR → save text workflow

### Orchestrator (`orchestrator/`)

Express server that acts as a GitHub Copilot Extension endpoint.

## GitHub Copilot Extension Setup

1. Create a GitHub App at https://github.com/settings/apps/new
2. Configure as Copilot Extension:
   - Set the endpoint URL to your orchestrator server
   - Enable Copilot Extension features
3. Install the app in your repository/organization

### Usage in Copilot

```
@testOrc run screen process
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | POST | Copilot Extension endpoint |
| `/health` | GET | Health check |
| `/agents` | GET | List available agents |

## Adding New Agents

1. Create agent file in `agents/`:

```javascript
// agents/my-agent.js
export const myAgentDefinition = {
  name: "my-agent",
  description: "Description of what the agent does",
  commands: ["my command", "another command"]
};

export async function myAgent(options = {}) {
  // Agent logic here
  return { success: true, message: "Done" };
}
```

2. Register in `agents/index.js`:

```javascript
import { myAgent, myAgentDefinition } from "./my-agent.js";

export const agents = {
  // ...existing agents
  "my-agent": {
    definition: myAgentDefinition,
    execute: myAgent
  }
};

export const commandMapping = {
  // ...existing mappings
  "my command": "my-agent"
};
```

## Adding New MCP Tools

1. Create tool in `mcp/tools/`:

```javascript
// mcp/tools/my-tool.js
export const myToolDefinition = {
  name: "my-tool",
  description: "What the tool does",
  inputSchema: {
    type: "object",
    properties: { /* ... */ },
    required: []
  }
};

export async function myTool(args) {
  // Tool logic
  return { success: true };
}
```

2. Register in `mcp/server.js` to expose via MCP protocol.

## Running MCP Server Standalone

```bash
npm run start:mcp
```

This starts the MCP server on stdio for use with MCP clients.
