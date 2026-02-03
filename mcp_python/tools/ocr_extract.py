"""
MCP2: OCR Extract Tool
Extracts text from a screenshot using EasyOCR and saves to text.txt
"""

import os
from pathlib import Path

from mcp.types import Tool

_reader = None


def _get_reader():
    """Create the EasyOCR reader lazily to avoid import-time failures."""
    global _reader
    if _reader is None:
        import easyocr

        # Initialize reader once (downloads models on first use to ~/.EasyOCR/)
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader

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

        try:
            reader = _get_reader()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": (
                    "OCR engine failed to initialize. This usually means Torch "
                    "is not available for this Python version. Use Python 3.11 "
                    "or install a compatible Torch wheel."
                )
            }

        # Perform OCR with EasyOCR. Returns (bbox, text, confidence) tuples.
        results = reader.readtext(image_path)

        # Extract text and confidences
        texts = []
        confidences = []
        for _bbox, text, confidence in results:
            texts.append(text)
            confidences.append(confidence)

        extracted_text = "\n".join(texts)
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
            "confidence": round(avg_confidence * 100, 2),
            "message": f"Text extracted and saved to {output_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to extract text from image"
        }
