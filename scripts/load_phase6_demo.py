#!/usr/bin/env python3
"""Load a minimal Phase 6 demo corpus via public GraphClerk HTTP APIs.

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


DEMO_META = {"demo_corpus": "phase_6", "created_by": "demo_loader"}

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = REPO_ROOT / "demo" / "phase6_demo_corpus.md"


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
        with urllib.request.urlopen(req, timeout=120) as resp:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Load Phase 6 demo corpus via GraphClerk APIs.")
    parser.add_argument(
        "--base-url",
        default=None,
        help="API base URL (overrides GRAPHCLERK_API_BASE_URL / default localhost:8000).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned HTTP calls only.")
    args = parser.parse_args()

    base = api_base_url(args.base_url)

    if not CORPUS_PATH.is_file():
        print(f"ERROR: corpus file missing: {CORPUS_PATH}", file=sys.stderr)
        return 1

    markdown = CORPUS_PATH.read_text(encoding="utf-8")
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    artifact_body = {
        "filename": "phase6_demo_corpus.md",
        "artifact_type": "markdown",
        "text": markdown,
        "title": f"Phase 6 demo corpus ({run_ts})",
        "mime_type": "text/markdown",
    }
    node_a_body = {
        "node_type": "concept",
        "label": f"Phase 6 demo — trace hub ({run_ts})",
        "summary": "Entry node for demo semantic index + evidence link.",
        "metadata": DEMO_META,
    }
    node_b_body = {
        "node_type": "concept",
        "label": f"Phase 6 demo — satellite ({run_ts})",
        "summary": "Second node for a directed edge.",
        "metadata": DEMO_META,
    }
    edge_body_template = {
        "from_node_id": "<graph_node_a_id>",
        "to_node_id": "<graph_node_b_id>",
        "relation_type": "explains",
        "summary": f"Demo edge ({run_ts})",
        "confidence": 0.85,
        "metadata": DEMO_META,
    }
    link_body_template = {
        "evidence_unit_id": "<evidence_unit_id>",
        "support_type": "supports",
        "confidence": 0.9,
    }
    si_body_template = {
        "meaning": f"Phase 6 demo routing anchor ({run_ts})",
        "summary": "Demo semantic index; vector_status likely pending until indexing runs.",
        "embedding_text": "Phase 6 demo corpus retrieval trace hook markdown paragraph.",
        "entry_node_ids": ["<graph_node_a_id>"],
        "metadata": DEMO_META,
    }

    print(f"API base: {base}")
    print(f"Run id (UTC label suffix): {run_ts}")
    print()

    if args.dry_run:
        art_preview = {**artifact_body, "text": f"<{len(markdown)} chars from {CORPUS_PATH.name}>"}
        print("[dry-run] Planned calls (no network I/O):")
        print(f"  1. POST {base}/artifacts")
        print(f"      {json.dumps(art_preview, indent=2)[:2500]}")
        print(f"  2. GET {base}/artifacts/<artifact_id>/evidence?limit=50&offset=0")
        print(f"  3. POST {base}/graph/nodes")
        print(f"      {json.dumps(node_a_body, indent=2)}")
        print(f"  4. POST {base}/graph/nodes")
        print(f"      {json.dumps(node_b_body, indent=2)}")
        print(f"  5. POST {base}/graph/edges")
        print(f"      {json.dumps(edge_body_template, indent=2)}")
        print(f"  6. POST {base}/graph/nodes/<graph_node_a_id>/evidence")
        print(f"      {json.dumps(link_body_template, indent=2)}")
        print(f"  7. POST {base}/semantic-indexes")
        print(f"      {json.dumps(si_body_template, indent=2)}")
        print()
        print("Dry run complete.")
        return 0

    art_url = f"{base}/artifacts"
    art_res = http_json("POST", art_url, artifact_body)
    if not isinstance(art_res, dict):
        print("ERROR: unexpected artifact response", file=sys.stderr)
        return 1
    artifact_id = art_res.get("artifact_id")
    eu_count = art_res.get("evidence_unit_count")
    print(f"Artifact: id={artifact_id} evidence_unit_count={eu_count}")

    ev_url = f"{base}/artifacts/{artifact_id}/evidence?limit=50&offset=0"
    ev_res = http_json("GET", ev_url, None)
    if not isinstance(ev_res, dict):
        print("ERROR: unexpected evidence list response", file=sys.stderr)
        return 1
    items = ev_res.get("items") or []
    if not items:
        print("ERROR: no evidence units returned after ingestion.", file=sys.stderr)
        return 1
    evidence_unit_id = items[0]["id"]
    print(f"Evidence unit (first): id={evidence_unit_id}")

    nodes_url = f"{base}/graph/nodes"
    node_a = http_json("POST", nodes_url, node_a_body)
    node_b = http_json("POST", nodes_url, node_b_body)
    if not isinstance(node_a, dict) or not isinstance(node_b, dict):
        print("ERROR: unexpected graph node response", file=sys.stderr)
        return 1
    node_a_id, node_b_id = node_a["id"], node_b["id"]
    print(f"GraphNode A: id={node_a_id}")
    print(f"GraphNode B: id={node_b_id}")

    edge_body = {
        "from_node_id": node_a_id,
        "to_node_id": node_b_id,
        "relation_type": "explains",
        "summary": f"Demo edge ({run_ts})",
        "confidence": 0.85,
        "metadata": DEMO_META,
    }
    edge_url = f"{base}/graph/edges"
    edge_res = http_json("POST", edge_url, edge_body)
    if not isinstance(edge_res, dict):
        print("ERROR: unexpected graph edge response", file=sys.stderr)
        return 1
    print(f"GraphEdge: id={edge_res['id']}")

    link_body = {
        "evidence_unit_id": evidence_unit_id,
        "support_type": "supports",
        "confidence": 0.9,
    }
    nev_url = f"{base}/graph/nodes/{node_a_id}/evidence"
    nev_res = http_json("POST", nev_url, link_body)
    if not isinstance(nev_res, dict):
        print("ERROR: unexpected node evidence response", file=sys.stderr)
        return 1
    print(f"GraphNodeEvidence: id={nev_res['id']} node={node_a_id} evidence={evidence_unit_id}")

    si_body = {
        "meaning": f"Phase 6 demo routing anchor ({run_ts})",
        "summary": "Demo semantic index; vector_status likely pending until indexing runs.",
        "embedding_text": "Phase 6 demo corpus retrieval trace hook markdown paragraph.",
        "entry_node_ids": [node_a_id],
        "metadata": DEMO_META,
    }
    si_url = f"{base}/semantic-indexes"
    si_res = http_json("POST", si_url, si_body)
    if not isinstance(si_res, dict):
        print("ERROR: unexpected semantic index response", file=sys.stderr)
        return 1
    print(f"SemanticIndex: id={si_res['id']} vector_status={si_res.get('vector_status')}")

    print()
    print("Done. See docs/demo/PHASE_6_DEMO_CORPUS.md for semantic-search limitations.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
