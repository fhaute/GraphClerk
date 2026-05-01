#!/usr/bin/env python3
"""Manual / dev backfill: embed ``SemanticIndex.embedding_text`` and upsert vectors to Qdrant.

Track B Slice B1 - does **not** auto-index on ``POST /semantic-indexes`` create.

Requires a working Postgres (``DATABASE_URL``) and Qdrant (``QDRANT_URL``) matching the API
configuration. Uses ``DeterministicFakeEmbeddingAdapter`` (dimension 8) for embeddings:
this is **dev/test quality**, not a semantic embedding model - see stderr notice.

Run from repository root (recommended)::

    # Set env vars (see backend/.env.example or Docker Compose)
    python scripts/backfill_semantic_indexes.py --help
    python scripts/backfill_semantic_indexes.py --semantic-index-id <UUID>
    python scripts/backfill_semantic_indexes.py --all-pending

Or from ``backend/`` with ``PYTHONPATH``::

    set PYTHONPATH=.
    python ..\\scripts\\backfill_semantic_indexes.py --all-pending
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill semantic index vectors (pending/failed to indexed or failed).",
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--semantic-index-id",
        type=str,
        metavar="UUID",
        help="Index a single semantic index by id.",
    )
    g.add_argument(
        "--all-pending",
        action="store_true",
        help="Index all rows in pending status (then failed up to --limit).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max rows to process for --all-pending (default 100).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-upsert even if the row is already indexed.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration and exit without connecting.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("dry-run: would load settings and run indexing (no DB/Qdrant calls).")
        return 0

    # Minimal env for Settings() if not already set (local convenience only).
    os.environ.setdefault("APP_NAME", "GraphClerk")
    os.environ.setdefault("APP_ENV", "local")
    os.environ.setdefault("LOG_LEVEL", "INFO")

    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is required.", file=sys.stderr)
        return 1
    if not os.getenv("QDRANT_URL"):
        print("ERROR: QDRANT_URL is required.", file=sys.stderr)
        return 1

    print(
        "NOTICE: embeddings use DeterministicFakeEmbeddingAdapter (8 dims) — dev/test only, not semantic quality.",
        file=sys.stderr,
    )

    from qdrant_client import QdrantClient

    from app.core import config as config_module
    from app.core.config import get_settings
    from app.db.session import get_sessionmaker
    from app.services.embedding_adapter import DeterministicFakeEmbeddingAdapter
    from app.services.embedding_service import EmbeddingService
    from app.services.semantic_index_service import SemanticIndexVectorIndexingService
    from app.services.vector_index_service import VectorIndexService

    config_module.get_settings.cache_clear()
    _ = get_settings()

    expected_dimension = 8
    embedding = EmbeddingService(
        adapter=DeterministicFakeEmbeddingAdapter(dimension=expected_dimension),
        expected_dimension=expected_dimension,
    )
    client = QdrantClient(url=get_settings().qdrant_url, api_key=get_settings().qdrant_api_key)
    vector = VectorIndexService(qdrant_client=client, expected_dimension=expected_dimension)

    SessionMaker = get_sessionmaker()
    with SessionMaker() as session:
        svc = SemanticIndexVectorIndexingService(
            session=session,
            embedding_service=embedding,
            vector_index_service=vector,
        )
        if args.semantic_index_id:
            sid = uuid.UUID(args.semantic_index_id)
            outcome = svc.index_semantic_index(semantic_index_id=sid, force=args.force)
            session.commit()
            print(f"{outcome.semantic_index_id} -> {outcome.status} ({outcome.detail or ''})".strip())
            return 0 if outcome.status != "failed" else 2

        outcomes = svc.index_all_pending(limit=args.limit, force=args.force)
        session.commit()
        for o in outcomes:
            print(f"{o.semantic_index_id} -> {o.status} ({o.detail or ''})".strip())
        failed_ct = sum(1 for o in outcomes if o.status == "failed")
        return 2 if failed_ct else 0


if __name__ == "__main__":
    raise SystemExit(main())
