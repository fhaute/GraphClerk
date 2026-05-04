#!/usr/bin/env python3
"""Load the large query-playground demo corpus via public GraphClerk HTTP APIs.

Ingests ``demo/query_playground_package/corpus_alice_in_wonderland.md`` (Project Gutenberg
#11, public domain), creates graph nodes + edge, links multiple evidence units to the
entry node, and registers a semantic index whose ``embedding_text`` matches
``GRAPHCLERK_LARGE_DEMO_QUERY_PLAYGROUND_V1`` (see corpus header).

Uses only stdlib. Does not modify the database directly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


DEMO_META = {"demo_corpus": "query_playground_large", "created_by": "query_playground_demo_loader"}

# Must match the token documented in ``corpus_alice_in_wonderland.md`` and used as
# ``embedding_text`` on the created semantic index (deterministic_fake routing).
ROUTING_ANCHOR = "GRAPHCLERK_LARGE_DEMO_QUERY_PLAYGROUND_V1"

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = REPO_ROOT / "demo" / "query_playground_package" / "corpus_alice_in_wonderland.md"


def api_base_url(cli_base: str | None) -> str:
    if cli_base:
        return cli_base.rstrip("/")
    return (
        os.environ.get("GRAPHCLERK_API_BASE_URL")
        or os.environ.get("GRAPHCLE_API_BASE_URL")
        or "http://localhost:8000"
    ).rstrip("/")


def http_json(method: str, url: str, body: dict | None = None) -> dict | list:
    data_bytes = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data_bytes = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return {}
            out = json.loads(raw)
            if not isinstance(out, (dict, list)):
                raise RuntimeError(f"Unexpected JSON top-level type from {url}")
            return out
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {e.reason} for {method} {url}: {err_body}") from e


def list_evidence_ids(base: str, artifact_id: str, *, page_size: int = 500) -> list[str]:
    out: list[str] = []
    offset = 0
    while True:
        url = f"{base}/artifacts/{artifact_id}/evidence?limit={page_size}&offset={offset}"
        res = http_json("GET", url, None)
        if not isinstance(res, dict):
            raise RuntimeError("unexpected evidence list response")
        items = res.get("items") or []
        for it in items:
            eid = it.get("id")
            if isinstance(eid, str):
                out.append(eid)
        if len(items) < page_size:
            break
        offset += page_size
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Load large query-playground demo package via GraphClerk APIs.")
    parser.add_argument(
        "--base-url",
        default=None,
        help="API base URL (overrides GRAPHCLERK_API_BASE_URL / default localhost:8000).",
    )
    parser.add_argument(
        "--corpus-path",
        type=Path,
        default=DEFAULT_CORPUS,
        help=f"Markdown corpus file (default: {DEFAULT_CORPUS})",
    )
    parser.add_argument(
        "--max-evidence-links",
        type=int,
        default=32,
        help="Max evidence units to link to the entry graph node (default: 32).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned HTTP calls only.")
    args = parser.parse_args()

    base = api_base_url(args.base_url)
    corpus_path: Path = args.corpus_path
    max_links = max(1, args.max_evidence_links)

    if not corpus_path.is_file():
        print(f"ERROR: corpus file missing: {corpus_path}", file=sys.stderr)
        return 1

    markdown = corpus_path.read_text(encoding="utf-8")
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    artifact_body = {
        "filename": "corpus_alice_in_wonderland.md",
        "artifact_type": "markdown",
        "text": markdown,
        "title": f"Query playground large demo - Alice (Gutenberg #11) ({run_ts})",
        "mime_type": "text/markdown",
    }
    node_a_body = {
        "node_type": "concept",
        "label": f"Large demo - entry / trace hub ({run_ts})",
        "summary": "Entry node for large demo semantic index + evidence links.",
        "metadata": DEMO_META,
    }
    node_b_body = {
        "node_type": "concept",
        "label": f"Large demo - satellite ({run_ts})",
        "summary": "Second node for a directed edge.",
        "metadata": DEMO_META,
    }

    print(f"API base: {base}")
    print(f"Corpus: {corpus_path} ({len(markdown)} chars)")
    print(f"Run id (UTC label suffix): {run_ts}")
    print(f"Routing anchor (paste as question with deterministic_fake): {ROUTING_ANCHOR}")
    print()

    if args.dry_run:
        art_preview = {**artifact_body, "text": f"<{len(markdown)} chars from {corpus_path.name}>"}
        print("[dry-run] Planned calls (no network I/O):")
        print(f"  1. POST {base}/artifacts")
        print(f"      {json.dumps(art_preview, indent=2)[:2800]}")
        print("  2. GET .../evidence (paginate), POST .../graph/nodes (x2), POST .../graph/edges")
        print(f"  3. POST .../graph/nodes/<entry>/evidence (up to {max_links} evidence units)")
        print(f"  4. POST {base}/semantic-indexes (embedding_text = routing anchor)")
        print()
        print("Dry run complete.")
        return 0

    art_res = http_json("POST", f"{base}/artifacts", artifact_body)
    if not isinstance(art_res, dict):
        print("ERROR: unexpected artifact response", file=sys.stderr)
        return 1
    artifact_id = art_res.get("artifact_id")
    eu_count = art_res.get("evidence_unit_count")
    print(f"Artifact: id={artifact_id} evidence_unit_count={eu_count}")

    ev_ids = list_evidence_ids(base, str(artifact_id))
    if not ev_ids:
        print("ERROR: no evidence units after ingestion.", file=sys.stderr)
        return 1
    link_ids = ev_ids[:max_links]
    print(f"Linking {len(link_ids)} evidence unit(s) to entry graph node (of {len(ev_ids)} total).")

    nodes_url = f"{base}/graph/nodes"
    node_a = http_json("POST", nodes_url, node_a_body)
    node_b = http_json("POST", nodes_url, node_b_body)
    if not isinstance(node_a, dict) or not isinstance(node_b, dict):
        print("ERROR: unexpected graph node response", file=sys.stderr)
        return 1
    node_a_id, node_b_id = node_a["id"], node_b["id"]
    print(f"GraphNode A (entry): id={node_a_id}")
    print(f"GraphNode B: id={node_b_id}")

    edge_body = {
        "from_node_id": node_a_id,
        "to_node_id": node_b_id,
        "relation_type": "explains",
        "summary": f"Large demo edge ({run_ts})",
        "confidence": 0.85,
        "metadata": DEMO_META,
    }
    edge_res = http_json("POST", f"{base}/graph/edges", edge_body)
    if not isinstance(edge_res, dict):
        print("ERROR: unexpected graph edge response", file=sys.stderr)
        return 1
    print(f"GraphEdge: id={edge_res['id']}")

    nev_url_base = f"{base}/graph/nodes/{node_a_id}/evidence"
    for i, eid in enumerate(link_ids):
        link_body = {"evidence_unit_id": eid, "support_type": "supports", "confidence": 0.9}
        nev_res = http_json("POST", nev_url_base, link_body)
        if not isinstance(nev_res, dict):
            print(f"ERROR: node evidence link failed at index {i}", file=sys.stderr)
            return 1
        if i == 0:
            print(f"GraphNodeEvidence (first): id={nev_res['id']} evidence={eid}")

    si_body = {
        "meaning": f"Large demo - Alice corpus ({run_ts})",
        "summary": "Gutenberg #11 + deterministic routing anchor; vector_status pending until backfill.",
        "embedding_text": ROUTING_ANCHOR,
        "entry_node_ids": [node_a_id],
        "metadata": DEMO_META,
    }
    si_res = http_json("POST", f"{base}/semantic-indexes", si_body)
    if not isinstance(si_res, dict):
        print("ERROR: unexpected semantic index response", file=sys.stderr)
        return 1
    print(f"SemanticIndex: id={si_res['id']} vector_status={si_res.get('vector_status')}")

    print()
    print("Next: index vectors so search can return this route, e.g.:")
    print(f'  python scripts/backfill_semantic_indexes.py --semantic-index-id "{si_res["id"]}"')
    print()
    print("Query playground (deterministic_fake): paste this exact question:")
    print(f"  {ROUTING_ANCHOR}")
    print()
    print("See demo/query_playground_package/README.md for details.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
