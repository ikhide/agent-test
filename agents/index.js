/**
 * Agents Registry
 * Central registry for all available agents
 */

import { screenAgent, screenAgentDefinition } from "./screen-agent.js";

// Register all agents here
export const agents = {
  "screen-agent": {
    definition: screenAgentDefinition,
    execute: screenAgent
  }
  // Add more agents here as they are created:
  // "data-agent": { definition: dataAgentDefinition, execute: dataAgent },
  // "review-agent": { definition: reviewAgentDefinition, execute: reviewAgent },
};

// Command to agent mapping
export const commandMapping = {
  "screen process": "screen-agent",
  "capture and extract": "screen-agent",
  "screenshot ocr": "screen-agent"
  // Add more command mappings here
};

export function getAgentForCommand(command) {
  const normalizedCommand = command.toLowerCase().trim();

  // Direct match
  if (commandMapping[normalizedCommand]) {
    return commandMapping[normalizedCommand];
  }

  // Partial match
  for (const [cmd, agentName] of Object.entries(commandMapping)) {
    if (normalizedCommand.includes(cmd) || cmd.includes(normalizedCommand)) {
      return agentName;
    }
  }

  return null;
}

export function listAgents() {
  return Object.entries(agents).map(([name, agent]) => ({
    name,
    description: agent.definition.description,
    commands: agent.definition.commands
  }));
}
