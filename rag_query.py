"""
Hybrid multimodal RAG — two indexes, best of both worlds:
  • Text chunks  → all-MiniLM-L6-v2  (strong semantic text retrieval)
  • Images       → clip-ViT-B-32      (cross-modal image ↔ text retrieval)
Flow: PDF → text chunks + page images → embed → two FAISS indexes (persistent) → retrieve
Usage: python3.11 rag_query.py --query "your question here"
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
from PIL import Image
import fitz  # PyMuPDF

load_dotenv()

# ── Args ──────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Hybrid multimodal RAG")
parser.add_argument("--query", required=True, help="Question to retrieve chunks for")
parser.add_argument("--k", type=int, default=4, help="Results per index (default: 4)")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR          = Path("/Users/godsonatakpu/Documents/dev/alstom/agent-test")
PDF_DIR           = BASE_DIR / "pdfs"
IMAGES_DIR        = BASE_DIR / "extracted_images"
TEXT_INDEX_DIR    = str(BASE_DIR / "faiss_index_text")
IMAGE_INDEX_DIR   = str(BASE_DIR / "faiss_index_images")
MANIFEST_PATH     = str(BASE_DIR / "faiss_manifest.json")

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ── Embeddings ────────────────────────────────────────────────────────────────

IMAGE_PREFIX = "__IMAGE__:"


class MiniLMEmbeddings(Embeddings):
    """all-MiniLM-L6-v2 — strong semantic text retrieval."""
    def __init__(self):
        print("🔢 Loading all-MiniLM-L6-v2 (~90MB on first run)...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("   Text embedding model ready — cost: $0")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(text, convert_to_numpy=True).tolist()


class CLIPEmbeddings(Embeddings):
    """clip-ViT-B-32 — cross-modal image ↔ text retrieval."""
    def __init__(self):
        print("🔢 Loading clip-ViT-B-32 (~350MB on first run)...")
        self.model = SentenceTransformer("clip-ViT-B-32")
        print("   CLIP model ready — cost: $0")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            if text.startswith(IMAGE_PREFIX):
                img = Image.open(text[len(IMAGE_PREFIX):]).convert("RGB")
                results.append(self.model.encode(img).tolist())
            else:
                results.append(self.model.encode(text).tolist())
        return results

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()


# ── Manifest ──────────────────────────────────────────────────────────────────

def load_manifest() -> set:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH) as f:
            return set(json.load(f))
    return set()


def save_manifest(files: set):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(list(files), f, indent=2)


# ── PDF processing ────────────────────────────────────────────────────────────

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def extract_text_chunks(pdf_path: str) -> list[Document]:
    pages = PyPDFLoader(pdf_path).load()
    return splitter.split_documents(pages)


def extract_images(pdf_path: str) -> list[Document]:
    docs = []
    pdf_name = Path(pdf_path).stem
    pdf_doc = fitz.open(pdf_path)
    for page_num, page in enumerate(pdf_doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = pdf_doc.extract_image(xref)
            img_path = IMAGES_DIR / f"{pdf_name}_p{page_num}_i{img_index}.{base_image['ext']}"
            img_path.write_bytes(base_image["image"])
            docs.append(Document(
                page_content=IMAGE_PREFIX + str(img_path),
                metadata={
                    "source": pdf_path,
                    "page": page_num,
                    "type": "image",
                    "image_path": str(img_path),
                },
            ))
    pdf_doc.close()
    return docs


def process_pdf(pdf_path: str) -> tuple[list[Document], list[Document]]:
    text_chunks = extract_text_chunks(pdf_path)
    image_docs  = extract_images(pdf_path)
    print(f"   • {Path(pdf_path).name}: {len(text_chunks)} text chunks, {len(image_docs)} images")
    return text_chunks, image_docs


# ── Index builder ─────────────────────────────────────────────────────────────

def build_or_update_index(
    index_dir: str,
    new_docs: list[Document],
    all_docs: list[Document],
    embeddings: Embeddings,
    label: str,
    has_existing: bool,
    has_new: bool,
) -> FAISS:
    if has_existing and not has_new:
        print(f"   [{label}] Loading existing index...")
        return FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
    elif has_existing and has_new:
        print(f"   [{label}] Updating index with {len(new_docs)} new item(s)...")
        store = FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
        store.add_documents(new_docs)
        store.save_local(index_dir)
        return store
    else:
        print(f"   [{label}] Building index from {len(all_docs)} item(s)...")
        store = FAISS.from_documents(all_docs, embeddings)
        store.save_local(index_dir)
        return store


# ── 1. Discover PDFs ──────────────────────────────────────────────────────────

pdf_files = list(PDF_DIR.glob("*.pdf"))
if not pdf_files:
    sys.exit(f"❌  No PDF files found in {PDF_DIR}")

print(f"📄 Found {len(pdf_files)} PDF file(s) in {PDF_DIR}")

# ── 2. Load embedding models ──────────────────────────────────────────────────

text_embeddings  = MiniLMEmbeddings()
image_embeddings = CLIPEmbeddings()

# ── 3. Determine new vs indexed files ─────────────────────────────────────────

indexed_files = load_manifest()
current_files = {str(f) for f in pdf_files}
new_files     = current_files - indexed_files

has_text_index  = os.path.exists(TEXT_INDEX_DIR)
has_image_index = os.path.exists(IMAGE_INDEX_DIR)
has_new         = bool(new_files)

# Process only new files (or all on first run)
files_to_process = new_files if (has_text_index or has_image_index) else current_files

all_text_chunks, all_image_docs = [], []
new_text_chunks, new_image_docs = [], []

if files_to_process:
    print(f"\n🔢 Processing {len(files_to_process)} file(s)...")
    for p in files_to_process:
        tc, imgs = process_pdf(p)
        if p in new_files:
            new_text_chunks.extend(tc)
            new_image_docs.extend(imgs)
        all_text_chunks.extend(tc)
        all_image_docs.extend(imgs)

# ── 4. Build / update indexes ─────────────────────────────────────────────────

print("\n📂 Syncing indexes...")

text_store = build_or_update_index(
    TEXT_INDEX_DIR, new_text_chunks, all_text_chunks,
    text_embeddings, "text", has_text_index, has_new,
)
image_store = build_or_update_index(
    IMAGE_INDEX_DIR, new_image_docs, all_image_docs,
    image_embeddings, "images", has_image_index, has_new,
)

if files_to_process:
    save_manifest(current_files)
    total = len(all_text_chunks) + len(all_image_docs)
    print(f"   Done. ({total} total items indexed)")

# ── 5. Retrieve ───────────────────────────────────────────────────────────────

text_retriever  = text_store.as_retriever(search_kwargs={"k": args.k})
image_retriever = image_store.as_retriever(search_kwargs={"k": args.k})

print("\n" + "═" * 60)
print(f"❓ Query: {args.query}")
print("═" * 60)

text_results  = text_retriever.invoke(args.query)
image_results = image_retriever.invoke(args.query)

print(f"\n── Text chunks (all-MiniLM-L6-v2) ──")
for i, doc in enumerate(text_results, 1):
    src  = Path(doc.metadata.get("source", "unknown")).name
    page = doc.metadata.get("page", "?")
    print(f"\n[T{i} — {src}, p.{page}]")
    print(f"  {doc.page_content[:400].strip()}")

print(f"\n── Image results (CLIP) ──")
if image_results:
    for i, doc in enumerate(image_results, 1):
        src  = Path(doc.metadata.get("source", "unknown")).name
        page = doc.metadata.get("page", "?")
        print(f"\n[I{i} — {src}, p.{page}]")
        print(f"  Image: {doc.metadata.get('image_path')}")
else:
    print("  No images found in indexed documents.")

print("\n" + "═" * 60)
print("Done.")
