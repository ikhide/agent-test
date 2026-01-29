/**
 * MCP2: OCR Extract Tool
 * Extracts text from a screenshot using Tesseract.js and saves to text.txt
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import Tesseract from "tesseract.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = path.join(__dirname, "../../output");

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

export const ocrExtractToolDefinition = {
  name: "ocr-extract-tool",
  description: "Extract text from a screenshot using OCR and save it to text.txt",
  inputSchema: {
    type: "object",
    properties: {
      imagePath: {
        type: "string",
        description: "Path to the screenshot image file"
      },
      outputFilename: {
        type: "string",
        description: "Output filename for extracted text (default: text.txt)"
      }
    },
    required: ["imagePath"]
  }
};

export async function ocrExtractTool(imagePath, outputFilename = "text.txt") {
  try {
    // Verify image exists
    if (!fs.existsSync(imagePath)) {
      return {
        success: false,
        error: "Image file not found",
        message: `Could not find image at: ${imagePath}`
      };
    }

    // Perform OCR
    const result = await Tesseract.recognize(imagePath, "eng", {
      logger: (m) => {
        if (m.status === "recognizing text") {
          process.stderr.write(`\rOCR Progress: ${Math.round(m.progress * 100)}%`);
        }
      }
    });

    const extractedText = result.data.text;
    const outputPath = path.join(OUTPUT_DIR, outputFilename);

    // Save extracted text to file
    fs.writeFileSync(outputPath, extractedText, "utf-8");

    return {
      success: true,
      imagePath: imagePath,
      outputPath: outputPath,
      textLength: extractedText.length,
      text: extractedText,
      confidence: result.data.confidence,
      message: `Text extracted and saved to ${outputPath}`
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      message: "Failed to extract text from image"
    };
  }
}
