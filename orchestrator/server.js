#!/usr/bin/env node

/**
 * Orchestrator Server
 * GitHub Copilot Extension that routes commands to agents
 *
 * Usage in GitHub Copilot: @testOrc run screen process
 */

import express from "express";
import { agents, getAgentForCommand, listAgents } from "../agents/index.js";

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

/**
 * GitHub Copilot Extension endpoint
 * Receives messages from Copilot and routes to appropriate agent
 */
app.post("/", async (req, res) => {
  try {
    const { messages } = req.body;

    if (!messages || !messages.length) {
      return res.json({
        choices: [{
          message: {
            role: "assistant",
            content: "No message received. Try: @testOrc run screen process"
          }
        }]
      });
    }

    const userMessage = messages[messages.length - 1]?.content || "";
    console.log(`[Orchestrator] Received: ${userMessage}`);

    // Parse command from message
    const command = parseCommand(userMessage);

    if (!command) {
      const agentList = listAgents();
      return res.json({
        choices: [{
          message: {
            role: "assistant",
            content: formatHelpMessage(agentList)
          }
        }]
      });
    }

    // Find agent for command
    const agentName = getAgentForCommand(command);

    if (!agentName) {
      return res.json({
        choices: [{
          message: {
            role: "assistant",
            content: `Unknown command: "${command}"\n\nAvailable commands:\n${listCommands()}`
          }
        }]
      });
    }

    // Execute agent
    console.log(`[Orchestrator] Routing to agent: ${agentName}`);
    const agent = agents[agentName];
    const result = await agent.execute();

    return res.json({
      choices: [{
        message: {
          role: "assistant",
          content: formatAgentResult(agentName, result)
        }
      }]
    });

  } catch (error) {
    console.error(`[Orchestrator] Error: ${error.message}`);
    return res.json({
      choices: [{
        message: {
          role: "assistant",
          content: `Error: ${error.message}`
        }
      }]
    });
  }
});

/**
 * Health check endpoint
 */
app.get("/health", (req, res) => {
  res.json({ status: "ok", agents: Object.keys(agents) });
});

/**
 * List agents endpoint
 */
app.get("/agents", (req, res) => {
  res.json({ agents: listAgents() });
});

/**
 * Parse command from user message
 * Extracts command after "run" keyword
 */
function parseCommand(message) {
  const runMatch = message.match(/run\s+(.+)/i);
  if (runMatch) {
    return runMatch[1].trim();
  }

  // Check if message itself is a known command
  const agentName = getAgentForCommand(message);
  if (agentName) {
    return message;
  }

  return null;
}

/**
 * Format help message
 */
function formatHelpMessage(agentList) {
  let help = "## Orchestrator Help\n\n";
  help += "**Usage:** `@testOrc run <command>`\n\n";
  help += "### Available Agents:\n\n";

  for (const agent of agentList) {
    help += `**${agent.name}**\n`;
    help += `  ${agent.description}\n`;
    help += `  Commands: ${agent.commands.map(c => `\`${c}\``).join(", ")}\n\n`;
  }

  help += "### Example:\n";
  help += "`@testOrc run screen process`";

  return help;
}

/**
 * List available commands
 */
function listCommands() {
  const agentList = listAgents();
  return agentList
    .flatMap(a => a.commands.map(c => `- ${c}`))
    .join("\n");
}

/**
 * Format agent execution result
 */
function formatAgentResult(agentName, result) {
  if (result.success) {
    let output = `## ${agentName} - Success\n\n`;
    output += `${result.message}\n\n`;

    if (result.screenshotPath) {
      output += `**Screenshot:** \`${result.screenshotPath}\`\n`;
    }
    if (result.textOutputPath) {
      output += `**Extracted Text:** \`${result.textOutputPath}\`\n`;
    }
    if (result.extractedTextLength) {
      output += `**Text Length:** ${result.extractedTextLength} characters\n`;
    }
    if (result.confidence) {
      output += `**OCR Confidence:** ${result.confidence.toFixed(1)}%\n`;
    }

    return output;
  } else {
    let output = `## ${agentName} - Failed\n\n`;
    output += `**Error:** ${result.message}\n`;
    if (result.error) {
      output += `**Details:** ${result.error}\n`;
    }
    return output;
  }
}

app.listen(PORT, () => {
  console.log(`[Orchestrator] Server running on http://localhost:${PORT}`);
  console.log(`[Orchestrator] Available agents: ${Object.keys(agents).join(", ")}`);
  console.log(`\nGitHub Copilot Extension endpoint: POST http://localhost:${PORT}/`);
  console.log(`Health check: GET http://localhost:${PORT}/health`);
  console.log(`List agents: GET http://localhost:${PORT}/agents`);
});
