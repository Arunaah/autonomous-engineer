"""
Qdrant Phase 2 — Semantic recall for failure patterns.
Falls back to PostgreSQL if Qdrant is unavailable.
"""
import os, logging, json
from typing import Optional

logger = logging.getLogger("ae.qdrant")

QDRANT_URL        = os.getenv("QDRANT_URL", "http://ae-qdrant:6333")
QDRANT_COLLECTION = "ae_failures"
EMBEDDING_DIM     = 384  # all-MiniLM-L6-v2


def _qdrant_client():
    from qdrant_client import QdrantClient
    return QdrantClient(url=QDRANT_URL, timeout=5)


def _embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def _ensure_collection():
    try:
        from qdrant_client.models import VectorParams, Distance
        client = _qdrant_client()
        existing = [c.name for c in client.get_collections().collections]
        if QDRANT_COLLECTION not in existing:
            client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=EMBEDDING_DIM,
                                            distance=Distance.COSINE))
            logger.info(f"Created Qdrant collection: {QDRANT_COLLECTION}")
    except Exception as e:
        logger.debug(f"Qdrant not available: {e}")


def store_failure_vector(failure_id: int, error_text: str,
                          fix_diff: str, confidence_delta: float):
    """Store failure + fix in Qdrant for semantic retrieval."""
    try:
        _ensure_collection()
        from qdrant_client.models import PointStruct
        client   = _qdrant_client()
        model    = _embedder()
        vector   = model.encode(error_text).tolist()
        payload  = {"failure_id":       failure_id,
                    "error_text":       error_text[:500],
                    "fix_diff":         fix_diff[:500],
                    "confidence_delta": confidence_delta}
        client.upsert(collection_name=QDRANT_COLLECTION,
                      points=[PointStruct(id=failure_id,
                                         vector=vector,
                                         payload=payload)])
        logger.info(f"Stored failure {failure_id} in Qdrant")
    except Exception as e:
        logger.debug(f"Qdrant store skipped (not available): {e}")


def search_similar_failures(error_text: str, limit: int = 3) -> list[dict]:
    """Semantic search for similar past failures and their fixes."""
    try:
        _ensure_collection()
        client  = _qdrant_client()
        model   = _embedder()
        vector  = model.encode(error_text).tolist()
        results = client.search(collection_name=QDRANT_COLLECTION,
                                query_vector=vector,
                                limit=limit,
                                score_threshold=0.7)
        hits = []
        for r in results:
            hits.append({**r.payload, "score": r.score})
        logger.info(f"Qdrant found {len(hits)} similar failures")
        return hits
    except Exception as e:
        logger.debug(f"Qdrant search skipped (not available): {e}")
        return []


def qdrant_available() -> bool:
    try:
        _qdrant_client().get_collections()
        return True
    except Exception:
        return False
