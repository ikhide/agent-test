"""
Small RAG script — single document, local embeddings (zero cost).
Flow: PyPDFLoader → chunk → HuggingFaceEmbeddings (local) → FAISS → retrieve
LLM step handled in Claude Code chat.
"""

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv()

PDF_PATH = "/Users/godsonatakpu/Documents/dev/alstom/agent-test/pdfs/Promisory Note With Obafemi complete.pdf"

# ── 1. Load PDF ───────────────────────────────────────────────────────────────

print("📄 Loading PDF...")
loader = PyPDFLoader(PDF_PATH)
pages = loader.load()
print(f"   Loaded {len(pages)} page(s)")

# ── 2. Chunk ──────────────────────────────────────────────────────────────────

print("✂️  Chunking document...")
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(pages)
print(f"   Created {len(chunks)} chunks")

# ── 3. Embed locally (zero cost) ──────────────────────────────────────────────

print("🔢 Embedding with local model (all-MiniLM-L6-v2)...")
print("   Downloading model on first run (~80MB), cached after...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
print("   Vector store ready — embedding cost: $0")

# ── 4. Retrieve relevant chunks (LLM step handled in chat) ───────────────────

questions = [
    "Who is the borrower in this promissory note?",
    "Who is the lender?",
    "What is the loan amount?",
    "What are the repayment terms?",
]

print("\n" + "═" * 60)
print("📋 Retrieved Chunks (answer these in chat)")
print("═" * 60)

for question in questions:
    print(f"\n❓ {question}")
    docs = retriever.invoke(question)
    for i, doc in enumerate(docs):
        print(f"  [Chunk {i+1}]: {doc.page_content[:300].strip()}")

print("\n" + "═" * 60)
print("Done.")
