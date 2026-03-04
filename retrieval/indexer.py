"""
Retrieval Layer — LlamaIndex + CodeBERT + Qdrant
Semantic codebase indexing for large multi-file repos.
This is what closes the gap with Claude Code on complex tasks.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

import structlog
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import CodeSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

log = structlog.get_logger()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION = os.getenv("QDRANT_COLLECTION", "codebase_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "microsoft/codebert-base")

# Supported code file extensions
CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs",
    ".java", ".cpp", ".c", ".h", ".cs", ".rb", ".php",
    ".yaml", ".yml", ".json", ".toml", ".md", ".sql"
}


def _get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def _ensure_collection(client: QdrantClient, vector_size: int = 768) -> None:
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        log.info("qdrant_collection_created", collection=COLLECTION)


def build_index(repo_path: str) -> VectorStoreIndex:
    """
    Build a full semantic index of a repository.
    Uses CodeBERT embeddings + Qdrant for storage.
    Called once per repo before the agent starts coding.
    """
    log.info("building_codebase_index", repo_path=repo_path)

    # Load only code files
    reader = SimpleDirectoryReader(
        input_dir=repo_path,
        recursive=True,
        required_exts=list(CODE_EXTENSIONS),
        exclude=["node_modules", ".git", "__pycache__", ".venv", "dist", "build"],
    )
    documents = reader.load_data()
    log.info("documents_loaded", count=len(documents))

    # CodeBERT embeddings (code-aware)
    embed_model = HuggingFaceEmbedding(
        model_name=EMBEDDING_MODEL,
        max_length=512,
    )
    Settings.embed_model = embed_model
    Settings.chunk_size = 512
    Settings.chunk_overlap = 64

    # Code-aware splitter (respects function/class boundaries)
    node_parser = CodeSplitter(
        language="python",  # fallback; LlamaIndex auto-detects per file
        chunk_lines=40,
        chunk_lines_overlap=5,
        max_chars=2048,
    )

    # Qdrant vector store
    client = _get_qdrant_client()
    _ensure_collection(client)
    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION)

    index = VectorStoreIndex.from_documents(
        documents,
        vector_store=vector_store,
        transformations=[node_parser],
        show_progress=True,
    )
    log.info("codebase_index_built", collection=COLLECTION)
    return index


def query_codebase(query: str, top_k: int = 10) -> str:
    """
    Query the semantic codebase index.
    Returns relevant code chunks as context for the agent.
    """
    client = _get_qdrant_client()
    embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL, max_length=512)
    Settings.embed_model = embed_model

    vector_store = QdrantVectorStore(client=client, collection_name=COLLECTION)
    index = VectorStoreIndex.from_vector_store(vector_store)
    retriever = index.as_retriever(similarity_top_k=top_k)

    nodes = retriever.retrieve(query)
    if not nodes:
        return "No relevant code found in codebase index."

    chunks = []
    for node in nodes:
        file_path = node.metadata.get("file_path", "unknown")
        chunks.append(f"### {file_path}\n```\n{node.text}\n```")

    return "\n\n".join(chunks)
