#!/usr/bin/env python3
"""Build `index.json` at repo root listing every protocol in the catalog.

Walks `protocols/<author>/<slug>/protocol.yaml`, pulls metadata, and emits
a single JSON file consumed by clients (the iOS app's catalog browser,
the rendered site, etc.). Stable schema:

    {
      "apiVersion": "hegemonikron.cogignition.cloud/v1",
      "kind": "Index",
      "generated_at": "2026-05-03T...",
      "protocols": [
        {
          "author":      "hooblarkhan",
          "slug":        "compound-fortnight",
          "title":       "Compound Fortnight",
          "description": "...",
          "license":     "CC-BY-4.0",
          "version":     "0.1",
          "created":     "2026-05-03",
          "references":  [...],
          "path":        "protocols/hooblarkhan/compound-fortnight/protocol.yaml",
          "raw_url":     "https://raw.githubusercontent.com/cogignition/protocols/main/protocols/hooblarkhan/compound-fortnight/protocol.yaml",
          "workflows":   ["morning_readiness", "in_flight_check", ...],
          "views":       ["hrv_trend", "rhr_drift", ...],
          "exercises":   ["pyramidal_compound", ...]
        },
        ...
      ]
    }

Sorted by author then slug for stable diffs. Run by CI on every push;
the app fetches the raw URL directly.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOLS_DIR = REPO_ROOT / "protocols"
INDEX_PATH = REPO_ROOT / "index.json"

RAW_URL_BASE = "https://raw.githubusercontent.com/cogignition/protocols/main/"


def main() -> int:
    entries: list[dict] = []

    for protocol_yaml in sorted(PROTOCOLS_DIR.rglob("protocol.yaml")):
        rel = protocol_yaml.relative_to(REPO_ROOT)
        # Path is protocols/<author>/<slug>/protocol.yaml
        parts = rel.parts
        if len(parts) != 4 or parts[0] != "protocols" or parts[3] != "protocol.yaml":
            print(f"  skipping (unexpected path): {rel}", file=sys.stderr)
            continue
        author, slug = parts[1], parts[2]

        with protocol_yaml.open() as f:
            doc = yaml.safe_load(f)

        meta = doc.get("metadata", {}) or {}
        # Sanity: author/slug in path must match metadata.
        if meta.get("author") != author or meta.get("id") != slug:
            print(
                f"  skipping (path/metadata mismatch): {rel} "
                f"(author={meta.get('author')!r} slug={meta.get('id')!r})",
                file=sys.stderr,
            )
            continue

        entry = {
            "author":      author,
            "slug":        slug,
            "title":       meta.get("title", slug),
            "description": (meta.get("description") or "").strip(),
            "license":     meta.get("license", "CC-BY-4.0"),
            "version":     meta.get("version"),
            "created":     str(meta.get("created")) if meta.get("created") else None,
            "references":  meta.get("references", []) or [],
            "path":        str(rel),
            "raw_url":     RAW_URL_BASE + str(rel),
            "workflows":   sorted((doc.get("workflows") or {}).keys()),
            "views":       [v.get("id") for v in (doc.get("views") or []) if v.get("id")],
            "exercises":   [e.get("id") for e in (doc.get("exercises") or []) if e.get("id")],
        }
        entries.append(entry)

    index = {
        "apiVersion": "hegemonikron.cogignition.cloud/v1",
        "kind":       "Index",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "protocols":  entries,
    }

    rendered = json.dumps(index, indent=2, sort_keys=False) + "\n"

    if "--check" in sys.argv:
        # CI mode: assert index.json on disk matches what we'd produce.
        # Ignores `generated_at` so timestamp drift doesn't cause spurious
        # failures.
        existing = INDEX_PATH.read_text() if INDEX_PATH.exists() else ""
        expected_norm = json.dumps({**index, "generated_at": "<ignored>"}, indent=2, sort_keys=False)
        try:
            existing_doc = json.loads(existing) if existing else {}
        except json.JSONDecodeError:
            existing_doc = {}
        existing_norm = json.dumps({**existing_doc, "generated_at": "<ignored>"}, indent=2, sort_keys=False)
        if existing_norm != expected_norm:
            print("ERROR: index.json is stale. Run `python tools/build_index.py` and commit.", file=sys.stderr)
            return 1
        print(f"index.json up to date ({len(entries)} protocol(s))")
        return 0

    INDEX_PATH.write_text(rendered)
    print(f"wrote {INDEX_PATH.relative_to(REPO_ROOT)} with {len(entries)} protocol(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
