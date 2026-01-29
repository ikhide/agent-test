---
name: screen-process
description: Capture screenshot and extract text via OCR
agent: screen-agent
tools: ["mcp:screen-capture/*"]
argument-hint: "Optional: custom filename for the screenshot"
---

# Screen Process Workflow

Execute the complete screen capture and OCR workflow:

1. Take a screenshot of the current desktop
2. Save it to the `snapshots/` folder
3. Extract all text from the screenshot using OCR
4. Save the extracted text to `output/text.txt`

${input:filename:Optional custom filename (default: screenshot-timestamp.png)}

Report the results including:
- Screenshot file path and size
- Extracted text file path
- Number of characters extracted
- OCR confidence percentage
