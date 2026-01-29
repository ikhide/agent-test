/**
 * MCP1: Snapshot Tool
 * Takes a screenshot of the desktop and saves it to snapshots folder
 */

import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SNAPSHOTS_DIR = path.join(__dirname, "../../snapshots");

// Ensure snapshots directory exists
if (!fs.existsSync(SNAPSHOTS_DIR)) {
  fs.mkdirSync(SNAPSHOTS_DIR, { recursive: true });
}

export const snapshotToolDefinition = {
  name: "snapshot-tool",
  description: "Take a screenshot of the desktop and save it to snapshots folder",
  inputSchema: {
    type: "object",
    properties: {
      filename: {
        type: "string",
        description: "Filename for the screenshot (e.g., 'screenshot.png')"
      }
    },
    required: ["filename"]
  }
};

export async function snapshotTool(filename) {
  try {
    const filePath = path.join(SNAPSHOTS_DIR, filename);
    const platform = process.platform;
    let command;

    if (platform === "darwin") {
      command = `screencapture -x "${filePath}"`;
    } else if (platform === "linux") {
      command = `import -window root "${filePath}"`;
    } else if (platform === "win32") {
      command = `powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object { $bitmap = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height); $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size); $bitmap.Save('${filePath}'); $graphics.Dispose(); $bitmap.Dispose() }"`;
    } else {
      throw new Error(`Unsupported platform: ${platform}`);
    }

    execSync(command, { stdio: "pipe" });

    const fileSize = fs.statSync(filePath).size;

    return {
      success: true,
      filePath: filePath,
      fileSize: fileSize,
      message: `Screenshot saved to ${filePath}`
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      message: "Failed to take screenshot"
    };
  }
}
