"""
Semantic Memory Router - Embedding-based recall for ELF.

Integrates semantic search into the ELF dashboard backend:
- POST /api/semantic/store - Store learning with embedding
- POST /api/semantic/recall - Query for relevant memories
- GET /api/semantic/health - Health check (Ollama status)
- GET /api/semantic/stats - Database statistics
- POST /api/semantic/migrate - Migrate existing heuristics

Uses Ollama with nomic-embed-text for embeddings.
Stores in the same database as other ELF data.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List
from pathlib import Path

import numpy as np
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils import get_db, dict_from_row

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/semantic", tags=["semantic"])

# Configuration
SEMANTIC_CONFIG_PATH = Path.home() / ".claude" / "emergent-learning" / "semantic" / "config.json"

# Default config (can be overridden by config.json)
DEFAULT_CONFIG = {
    "embeddingModel": "nomic-embed-text",
    "minSimilarity": 0.45,
    "maxResults": 3,
    "duplicateThreshold": 0.92,
    "timeoutMs": 2500,
    "ollamaUrl": "http://localhost:11434/api/embeddings"
}

# Load config
def load_config():
    """Load semantic config, falling back to defaults."""
    try:
        if SEMANTIC_CONFIG_PATH.exists():
            with open(SEMANTIC_CONFIG_PATH) as f:
                user_config = json.load(f)
                return {**DEFAULT_CONFIG, **user_config}
    except Exception as e:
        logger.warning(f"Failed to load semantic config: {e}")
    return DEFAULT_CONFIG

CONFIG = load_config()

# ConnectionManager for WebSocket broadcasts
manager = None

def set_manager(m):
    """Set the ConnectionManager for broadcasting updates."""
    global manager
    manager = m


# =============================================================================
# Database Schema Extension
# =============================================================================

def init_semantic_tables(conn):
    """Initialize semantic memory tables."""
    cursor = conn.cursor()

    # Semantic embeddings table - stores embeddings for any content
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semantic_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,  -- 'heuristic', 'learning', 'session', 'custom'
            source_id INTEGER,          -- Reference to source table (if applicable)
            content TEXT NOT NULL,      -- The text that was embedded
            context TEXT,               -- Additional context
            embedding BLOB NOT NULL,    -- JSON-encoded embedding vector
            confidence REAL DEFAULT 0.9,
            session_source TEXT,        -- Session ID if applicable
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Indexes for efficient queries
            UNIQUE(source_type, source_id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_semantic_type
        ON semantic_embeddings(source_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_semantic_created
        ON semantic_embeddings(created_at DESC)
    """)

    conn.commit()


# =============================================================================
# Embedding Functions
# =============================================================================

def embed(text: str) -> List[float]:
    """Generate embedding using Ollama."""
    try:
        resp = requests.post(
            CONFIG.get("ollamaUrl", DEFAULT_CONFIG["ollamaUrl"]),
            json={
                "model": CONFIG["embeddingModel"],
                "prompt": text
            },
            timeout=CONFIG["timeoutMs"] / 1000
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Embedding failed (is Ollama running?): {e}")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_np = np.array(a)
    b_np = np.array(b)
    dot_product = np.dot(a_np, b_np)
    norm_a = np.linalg.norm(a_np)
    norm_b = np.linalg.norm(b_np)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


# =============================================================================
# Pydantic Models
# =============================================================================

class StoreRequest(BaseModel):
    type: str  # 'heuristic', 'learning', 'session', 'custom'
    content: str
    context: Optional[str] = None
    confidence: Optional[float] = 0.9
    session_source: Optional[str] = None
    source_id: Optional[int] = None


class RecallRequest(BaseModel):
    query: str
    minSimilarity: Optional[float] = None
    maxResults: Optional[int] = None
    type_filter: Optional[str] = None  # Filter by source_type


class StoreResponse(BaseModel):
    status: str
    id: Optional[int] = None
    type: Optional[str] = None
    confidence: Optional[float] = None
    existing_id: Optional[int] = None
    existing_content: Optional[str] = None
    similarity: Optional[float] = None


class MemoryResult(BaseModel):
    id: int
    type: str
    content: str
    context: Optional[str]
    confidence: float
    created_at: str
    similarity: float


class RecallResponse(BaseModel):
    memories: List[MemoryResult]
    count: int
    query: str


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/health")
async def health():
    """Health check endpoint - verifies Ollama connectivity."""
    ollama_ok = False
    model_available = False

    try:
        # Check Ollama is running
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            ollama_ok = True
            # Check if model is available
            models = resp.json().get("models", [])
            model_available = any(
                m.get("name", "").startswith(CONFIG["embeddingModel"])
                for m in models
            )
    except Exception:
        pass

    # Check database
    db_ok = False
    try:
        with get_db() as conn:
            init_semantic_tables(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM semantic_embeddings")
            db_ok = True
    except Exception:
        pass

    status = "ok" if (ollama_ok and db_ok and model_available) else "degraded"

    return {
        "status": status,
        "ollama": ollama_ok,
        "model": CONFIG["embeddingModel"],
        "model_available": model_available,
        "database": db_ok,
        "config": {
            "minSimilarity": CONFIG["minSimilarity"],
            "maxResults": CONFIG["maxResults"]
        }
    }


@router.post("/store", response_model=StoreResponse)
async def store(request: StoreRequest):
    """Store a new learning with its embedding."""
    try:
        embedding = embed(request.content)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    with get_db() as conn:
        init_semantic_tables(conn)
        cursor = conn.cursor()

        # Check for duplicates by similarity
        cursor.execute("SELECT id, content, embedding FROM semantic_embeddings")
        for row in cursor.fetchall():
            existing_embedding = json.loads(row["embedding"])
            sim = cosine_similarity(embedding, existing_embedding)
            if sim >= CONFIG["duplicateThreshold"]:
                return StoreResponse(
                    status="duplicate",
                    existing_id=row["id"],
                    existing_content=row["content"],
                    similarity=round(sim, 4)
                )

        # Store new learning
        cursor.execute("""
            INSERT INTO semantic_embeddings
            (source_type, source_id, content, context, embedding, confidence, session_source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.type,
            request.source_id,
            request.content,
            request.context,
            json.dumps(embedding),
            request.confidence,
            request.session_source
        ))

        learning_id = cursor.lastrowid
        conn.commit()

        # Broadcast update if manager available
        if manager:
            await manager.broadcast_update("semantic_stored", {
                "id": learning_id,
                "type": request.type
            })

        return StoreResponse(
            status="stored",
            id=learning_id,
            type=request.type,
            confidence=request.confidence
        )


@router.post("/recall", response_model=RecallResponse)
async def recall(request: RecallRequest):
    """Query for relevant memories by semantic similarity."""
    try:
        query_embedding = embed(request.query)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    min_similarity = request.minSimilarity or CONFIG["minSimilarity"]
    max_results = request.maxResults or CONFIG["maxResults"]

    with get_db() as conn:
        init_semantic_tables(conn)
        cursor = conn.cursor()

        # Build query with optional type filter
        query = """
            SELECT id, source_type, content, context, embedding, confidence, created_at
            FROM semantic_embeddings
        """
        params = []

        if request.type_filter:
            query += " WHERE source_type = ?"
            params.append(request.type_filter)

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            stored_embedding = json.loads(row["embedding"])
            sim = cosine_similarity(query_embedding, stored_embedding)

            if sim >= min_similarity:
                results.append(MemoryResult(
                    id=row["id"],
                    type=row["source_type"],
                    content=row["content"],
                    context=row["context"],
                    confidence=row["confidence"],
                    created_at=row["created_at"],
                    similarity=round(sim, 4)
                ))

        # Sort by similarity and limit
        results.sort(key=lambda x: x.similarity, reverse=True)
        results = results[:max_results]

        return RecallResponse(
            memories=results,
            count=len(results),
            query=request.query
        )


@router.get("/stats")
async def stats():
    """Get semantic memory statistics."""
    with get_db() as conn:
        init_semantic_tables(conn)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM semantic_embeddings")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT source_type, COUNT(*) as count
            FROM semantic_embeddings
            GROUP BY source_type
        """)
        by_type = {row["source_type"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT COUNT(*) FROM semantic_embeddings
            WHERE created_at >= datetime('now', '-7 days')
        """)
        recent = cursor.fetchone()[0]

        return {
            "total_embeddings": total,
            "by_type": by_type,
            "last_7_days": recent,
            "config": {
                "model": CONFIG["embeddingModel"],
                "minSimilarity": CONFIG["minSimilarity"],
                "maxResults": CONFIG["maxResults"]
            }
        }


@router.post("/migrate-heuristics")
async def migrate_heuristics():
    """
    Migrate existing ELF heuristics to semantic memory.
    One-time operation to bootstrap semantic search for existing data.
    """
    with get_db() as conn:
        init_semantic_tables(conn)
        cursor = conn.cursor()

        # Get heuristics that don't have embeddings yet
        cursor.execute("""
            SELECT h.id, h.domain, h.rule, h.explanation, h.confidence
            FROM heuristics h
            LEFT JOIN semantic_embeddings se
                ON se.source_type = 'heuristic' AND se.source_id = h.id
            WHERE se.id IS NULL
            ORDER BY h.created_at DESC
            LIMIT 100
        """)

        heuristics = cursor.fetchall()

        migrated = 0
        duplicates = 0
        errors = 0

        for h in heuristics:
            try:
                # Create embeddable text
                full_text = f"[{h['domain']}] {h['rule']}"
                if h['explanation']:
                    full_text += f" - {h['explanation']}"

                embedding = embed(full_text)

                # Check for duplicates
                cursor.execute("SELECT id, embedding FROM semantic_embeddings")
                is_duplicate = False

                for row in cursor.fetchall():
                    existing_embedding = json.loads(row["embedding"])
                    sim = cosine_similarity(embedding, existing_embedding)
                    if sim >= CONFIG["duplicateThreshold"]:
                        is_duplicate = True
                        duplicates += 1
                        break

                if not is_duplicate:
                    cursor.execute("""
                        INSERT INTO semantic_embeddings
                        (source_type, source_id, content, context, embedding, confidence, session_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "heuristic",
                        h["id"],
                        h["rule"],
                        f"Domain: {h['domain']}",
                        json.dumps(embedding),
                        h["confidence"] or 0.85,
                        "migrated_from_heuristics"
                    ))
                    conn.commit()
                    migrated += 1

            except Exception as e:
                logger.error(f"Migration error for heuristic {h['id']}: {e}")
                errors += 1

        return {
            "status": "migration_complete",
            "migrated": migrated,
            "duplicates": duplicates,
            "errors": errors,
            "remaining": len(heuristics) - migrated - duplicates - errors
        }


@router.delete("/clear")
async def clear_embeddings(confirm: bool = False):
    """Clear all semantic embeddings. Requires confirm=true."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Pass confirm=true to clear all embeddings"
        )

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM semantic_embeddings")
        deleted = cursor.rowcount
        conn.commit()

        return {
            "status": "cleared",
            "deleted_count": deleted
        }
