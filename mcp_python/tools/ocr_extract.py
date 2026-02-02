"""
MCP2: OCR Extract Tool
Extracts text from a screenshot using pytesseract and saves to text.txt
"""

import os
from pathlib import Path

import pytesseract
from PIL import Image
from mcp.types import Tool

# Get the directory paths
TOOLS_DIR = Path(__file__).parent
OUTPUT_DIR = TOOLS_DIR.parent.parent / "output"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ocr_extract_tool_definition = Tool(
    name="ocr-extract-tool",
    description="Extract text from a screenshot using OCR and save it to text.txt",
    inputSchema={
        "type": "object",
        "properties": {
            "imagePath": {
                "type": "string",
                "description": "Path to the screenshot image file"
            },
            "outputFilename": {
                "type": "string",
                "description": "Output filename for extracted text (default: text.txt)"
            }
        },
        "required": ["imagePath"]
    }
)


async def ocr_extract_tool(image_path: str, output_filename: str = "text.txt") -> dict:
    """Extract text from an image using OCR and save it to a file."""
    try:
        # Verify image exists
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": "Image file not found",
                "message": f"Could not find image at: {image_path}"
            }

        # Open image and perform OCR
        image = Image.open(image_path)

        # Perform OCR with pytesseract
        ocr_data = pytesseract.image_to_data(image, lang="eng", output_type=pytesseract.Output.DICT)
        extracted_text = pytesseract.image_to_string(image, lang="eng")

        # Calculate confidence (average of non-empty confidences)
        confidences = [c for c, t in zip(ocr_data["conf"], ocr_data["text"]) if t.strip() and c != -1]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        output_path = OUTPUT_DIR / output_filename

        # Save extracted text to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        return {
            "success": True,
            "imagePath": image_path,
            "outputPath": str(output_path),
            "textLength": len(extracted_text),
            "text": extracted_text,
            "confidence": round(avg_confidence, 2),
            "message": f"Text extracted and saved to {output_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to extract text from image"
        }
