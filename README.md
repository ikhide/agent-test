# Copilot Multi-Agent Orchestrator

A multi-agent orchestration system using GitHub Copilot's native agent files (`.agent.md`) and MCP tools.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     GitHub Copilot Chat                          │
│                                                                  │
│   User: "run screen process"                                     │
│   Agent Dropdown: [orchestrator ▼]                               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                                │
│                  (orchestrator.agent.md)                         │
│                                                                  │
│   • Receives user commands                                       │
│   • Routes to appropriate sub-agent                              │
│   • Ensures consistent workflow execution                        │
│   • Coordinates multi-agent sequences                            │
└──────────────────────────┬───────────────────────────────────────┘
                           │ handoff
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                       AGENTS LAYER                               │
├────────────────────┬─────────────────────┬───────────────────────┤
│   screen-agent     │    data-agent       │     agent-n           │
│   (implemented)    │    (future)         │     (future)          │
│                    │                     │                       │
│   Screenshot +     │    Data analysis    │     Custom            │
│   OCR workflow     │    workflows        │     workflows         │
└─────────┬──────────┴─────────────────────┴───────────────────────┘
          │ handoff back
          ▼
┌──────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                                │
│                  (ready for next command)                        │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow (Hub-and-Spoke Pattern)

```
User Command
     │
     ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│ Orchestrator│─────►│ Screen Agent │─────►│ Orchestrator│
│   (route)   │      │  (execute)   │      │  (next?)    │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                     ┌──────┴──────┐
                     ▼             ▼
                  ┌─────┐      ┌─────┐
                  │MCP1 │      │MCP2 │
                  │snap-│      │ocr- │
                  │shot │      │extract│
                  └──┬──┘      └──┬──┘
                     │            │
                     ▼            ▼
               snapshots/    output/text.txt
```

**Why Hub-and-Spoke?**
- Orchestrator maintains control of the entire workflow
- Consistent execution across all agents
- Easy to add new agents without changing existing ones
- Clear audit trail of which agent did what

## Project Structure

```
agent-test/
├── .github/
│   └── agents/
│       ├── orchestrator.agent.md    # Parent orchestrator
│       └── screen-agent.agent.md    # Screenshot + OCR agent
├── .vscode/
│   └── mcp.json                     # MCP server configuration
├── mcp/
│   ├── server.js                    # MCP server (stdio)
│   └── tools/
│       ├── snapshot.js              # MCP1: Screenshot tool
│       └── ocr-extract.js           # MCP2: OCR extraction tool
├── snapshots/                       # Screenshot output
├── output/                          # Text extraction output
└── package.json
```

## Components

### 1. Orchestrator Agent

**File:** `.github/agents/orchestrator.agent.md`

The parent agent that:
- Receives all user commands
- Routes to appropriate sub-agents via handoffs
- Waits for sub-agents to complete and return
- Coordinates multi-step workflows

### 2. Screen Agent

**File:** `.github/agents/screen-agent.agent.md`

A specialized agent that:
- Takes screenshots using `snapshot-tool` (MCP1)
- Extracts text using `ocr-extract-tool` (MCP2)
- Saves results to `output/text.txt`
- Returns control to orchestrator when done

### 3. MCP Tools

**Location:** `mcp/tools/`

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `snapshot-tool` | Captures desktop screenshot | `filename` | `filePath`, `fileSize` |
| `ocr-extract-tool` | Extracts text from image | `imagePath`, `outputFilename` | `text`, `confidence` |

### 4. MCP Server

**File:** `mcp/server.js`

Exposes tools via the Model Context Protocol (stdio transport). Configured in `.vscode/mcp.json`.

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Open in VS Code
code .

# 3. Open Copilot Chat (Ctrl+Shift+I or Cmd+Shift+I)

# 4. Select "orchestrator" from the agent dropdown

# 5. Type your command
run screen process
```

## Usage

### Using the Orchestrator (Recommended)

1. Open **Copilot Chat** panel in VS Code
2. Click the **agent dropdown** at the top
3. Select **"orchestrator"**
4. Type: `run screen process`

### Using Screen Agent Directly

1. Select **"screen-agent"** from dropdown
2. Type: `capture and extract text`

## Adding New Agents

### Step 1: Create Agent File

Create `.github/agents/my-agent.agent.md`:

```markdown
---
name: my-agent
description: What this agent does
tools: ["my-mcp-server/*"]
infer: false
handoffs:
  - label: "Return to Orchestrator"
    agent: "orchestrator"
    prompt: "Task completed. Ready for next command."
---

# My Agent

Instructions for the agent...

## Workflow Steps

1. Step one
2. Step two
3. Return to orchestrator
```

### Step 2: Register with Orchestrator

Add handoff in `.github/agents/orchestrator.agent.md`:

```yaml
handoffs:
  - label: "Screen Process"
    agent: "screen-agent"
    prompt: "Execute the screen capture and OCR workflow"
  - label: "My New Task"
    agent: "my-agent"
    prompt: "Execute the new workflow"
```

### Step 3: Update Command Routing

Add routing instructions in orchestrator's markdown body.

## Adding New MCP Tools

### Step 1: Create Tool

Create `mcp/tools/my-tool.js`:

```javascript
export const myToolDefinition = {
  name: "my-tool",
  description: "What it does",
  inputSchema: {
    type: "object",
    properties: {
      param1: { type: "string", description: "Description" }
    },
    required: ["param1"]
  }
};

export async function myTool(param1) {
  // Implementation
  return { success: true, result: "..." };
}
```

### Step 2: Register in MCP Server

Update `mcp/server.js`:

```javascript
import { myToolDefinition, myTool } from "./tools/my-tool.js";

// Add to tools array
const tools = [snapshotToolDefinition, ocrExtractToolDefinition, myToolDefinition];

// Add case in switch
case "my-tool":
  result = await myTool(args.param1);
  break;
```

## File Formats Reference

| File | Location | Purpose |
|------|----------|---------|
| `*.agent.md` | `.github/agents/` | Define agent personas, tools, and handoffs |
| `mcp.json` | `.vscode/` | Configure MCP servers for VS Code |

### Agent File Schema

```yaml
---
name: agent-name              # Identifier
description: What it does     # Shown in dropdown
tools: ["tool1", "mcp/*"]     # Available tools
infer: true|false             # Auto-select based on context
handoffs:                     # Agents it can delegate to
  - label: "Display Name"
    agent: "target-agent"
    prompt: "Instructions for handoff"
---

# Markdown instructions for the agent
```

## Documentation & Resources

### GitHub Copilot Custom Agents

- [Custom Agents in VS Code](https://code.visualstudio.com/docs/copilot/customization/custom-agents) - Creating and configuring agents
- [Custom Agents Configuration Reference](https://docs.github.com/en/copilot/reference/custom-agents-configuration) - YAML schema
- [How to Write a Great AGENTS.md](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) - Best practices

### Model Context Protocol (MCP)

- [MCP Specification](https://modelcontextprotocol.io/) - Official protocol docs
- [Extending Copilot Chat with MCP](https://docs.github.com/copilot/customizing-copilot/using-model-context-protocol/extending-copilot-chat-with-mcp) - VS Code integration
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers) - Example servers

### Tutorials

- [Agents Tutorial](https://code.visualstudio.com/docs/copilot/agents/agents-tutorial) - Step-by-step guide
- [Enhance Agent Mode with MCP](https://docs.github.com/en/copilot/tutorials/enhance-agent-mode-with-mcp) - MCP integration tutorial

## Troubleshooting

### Agents not appearing in dropdown

1. Ensure files are in `.github/agents/` folder
2. Check file extension is `.agent.md`
3. Verify YAML frontmatter is valid
4. Reload VS Code window

### MCP tools not working

1. Check `.vscode/mcp.json` configuration
2. Run `npm install` to ensure dependencies
3. Verify MCP server starts: `npm run start:mcp`
4. Check VS Code Output panel for errors

### Handoffs not working

1. Ensure target agent exists in `.github/agents/`
2. Verify handoff schema has `label`, `agent`, and `prompt`
3. Check agent names match exactly
