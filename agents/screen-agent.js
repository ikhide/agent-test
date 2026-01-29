/**
 * Screen Agent
 * Coordinates MCP1 (snapshot) and MCP2 (ocr-extract) to:
 * 1. Take a screenshot
 * 2. Extract text from it
 * 3. Save to text.txt
 */

import { snapshotTool } from "../mcp/tools/snapshot.js";
import { ocrExtractTool } from "../mcp/tools/ocr-extract.js";

export const screenAgentDefinition = {
  name: "screen-agent",
  description: "Takes a screenshot and extracts text from it using OCR",
  commands: ["screen process", "capture and extract", "screenshot ocr"]
};

export async function screenAgent(options = {}) {
  const timestamp = Date.now();
  const filename = options.filename || `screenshot-${timestamp}.png`;
  const outputFilename = options.outputFilename || "text.txt";

  const steps = [];

  try {
    // Step 1: Take screenshot using MCP1
    console.error(`[Screen Agent] Step 1: Taking screenshot...`);
    const snapshotResult = await snapshotTool(filename);

    steps.push({
      step: 1,
      tool: "snapshot-tool",
      status: snapshotResult.success ? "success" : "failed",
      result: snapshotResult
    });

    if (!snapshotResult.success) {
      return {
        success: false,
        agent: "screen-agent",
        message: "Failed at step 1: Could not take screenshot",
        steps
      };
    }

    // Step 2: Extract text using MCP2
    console.error(`[Screen Agent] Step 2: Extracting text from screenshot...`);
    const ocrResult = await ocrExtractTool(snapshotResult.filePath, outputFilename);

    steps.push({
      step: 2,
      tool: "ocr-extract-tool",
      status: ocrResult.success ? "success" : "failed",
      result: ocrResult
    });

    if (!ocrResult.success) {
      return {
        success: false,
        agent: "screen-agent",
        message: "Failed at step 2: Could not extract text",
        steps
      };
    }

    // Success
    return {
      success: true,
      agent: "screen-agent",
      message: `Screenshot captured and text extracted successfully`,
      screenshotPath: snapshotResult.filePath,
      textOutputPath: ocrResult.outputPath,
      extractedTextLength: ocrResult.textLength,
      confidence: ocrResult.confidence,
      steps
    };

  } catch (error) {
    return {
      success: false,
      agent: "screen-agent",
      error: error.message,
      message: "Agent encountered an unexpected error",
      steps
    };
  }
}
