"""
MCP1: Snapshot Tool
Takes a screenshot of the desktop and saves it to snapshots folder
"""

import os
import sys
import subprocess
from pathlib import Path

from mcp.types import Tool

# Get the directory paths
TOOLS_DIR = Path(__file__).parent
SNAPSHOTS_DIR = TOOLS_DIR.parent.parent / "snapshots"

# Ensure snapshots directory exists
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

snapshot_tool_definition = Tool(
    name="snapshot-tool",
    description="Take a screenshot of the desktop and save it to snapshots folder",
    inputSchema={
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Filename for the screenshot (e.g., 'screenshot.png')"
            }
        },
        "required": ["filename"]
    }
)


async def snapshot_tool(filename: str) -> dict:
    """Take a screenshot and save it to the snapshots folder."""
    try:
        file_path = SNAPSHOTS_DIR / filename
        platform = sys.platform

        if platform == "darwin":
            command = ["screencapture", "-x", str(file_path)]
        elif platform == "linux":
            command = ["import", "-window", "root", str(file_path)]
        elif platform == "win32":
            # PowerShell command for Windows screenshot
            ps_script = f"""
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object {{
                $bitmap = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size)
                $bitmap.Save('{file_path}')
                $graphics.Dispose()
                $bitmap.Dispose()
            }}
            """
            command = ["powershell", "-Command", ps_script]
        else:
            raise OSError(f"Unsupported platform: {platform}")

        subprocess.run(command, check=True, capture_output=True)

        file_size = os.path.getsize(file_path)

        return {
            "success": True,
            "filePath": str(file_path),
            "fileSize": file_size,
            "message": f"Screenshot saved to {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to take screenshot"
        }
