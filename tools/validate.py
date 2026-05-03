#!/usr/bin/env python3
"""Validate protocols in this catalog against the Hegemonikron Spec.

Used by both the GitHub Actions CI workflow and local pre-commit checks.
Walks `protocols/**/protocol.yaml` (or a single path if given as an
argument), and for each file:

    1. Validates against schema/protocol.schema.json from the spec.
    2. Cross-references every input metric against vocabulary.yaml.
    3. Asserts metadata.license is in the allowed set.
    4. Asserts the file path matches metadata.author and metadata.id.

Exits 0 if all checks pass, 1 otherwise. Prints one line per file
checked.

Usage:
    python tools/validate.py                   # validates all protocols
    python tools/validate.py protocols/.../protocol.yaml   # single file
    SPEC_REF=v0.1 python tools/validate.py     # pin spec to tag/SHA
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml not installed. Run: pip install pyyaml jsonschema")

try:
    import jsonschema
except ImportError:
    sys.exit("ERROR: jsonschema not installed. Run: pip install pyyaml jsonschema")


REPO_ROOT = Path(__file__).resolve().parent.parent

# Schemas are bundled in `spec/` so this repo doesn't depend on a
# private upstream. Update the bundled copies when the canonical
# schema in the (private) spec repo changes.
SPEC_DIR = REPO_ROOT / "spec"

ALLOWED_LICENSES = {"CC-BY-4.0", "CC-BY-SA-4.0", "CC0-1.0", "Apache-2.0"}

PATH_PATTERN = re.compile(
    r"^protocols/(?P<author>[a-z0-9][a-z0-9-]*)/(?P<slug>[a-z0-9][a-z0-9-]*)/protocol\.yaml$"
)


def load_spec() -> tuple[dict, dict]:
    """Load the bundled protocol schema + vocabulary."""
    schema = json.loads((SPEC_DIR / "protocol.schema.json").read_text())
    vocab = yaml.safe_load((SPEC_DIR / "vocabulary.yaml").read_text())
    return schema, vocab


def check_path(rel_path: str, doc: dict) -> list[str]:
    """Verify rel_path matches metadata.author and metadata.id."""
    errors = []
    m = PATH_PATTERN.match(rel_path)
    if not m:
        errors.append(
            f"path '{rel_path}' does not match "
            f"protocols/<author>/<slug>/protocol.yaml"
        )
        return errors
    md = doc.get("metadata", {})
    if md.get("author") != m.group("author"):
        errors.append(
            f"metadata.author '{md.get('author')}' does not match "
            f"path author '{m.group('author')}'"
        )
    if md.get("id") != m.group("slug"):
        errors.append(
            f"metadata.id '{md.get('id')}' does not match "
            f"path slug '{m.group('slug')}'"
        )
    return errors


def check_vocabulary(doc: dict, vocab: dict) -> list[str]:
    """Every inputs[*].metric must exist in the vocabulary."""
    errors = []
    declared = set(vocab.get("metrics", {}).keys())
    for name, spec in doc.get("inputs", {}).items():
        metric = spec.get("metric")
        if metric and metric not in declared:
            errors.append(
                f"input '{name}' references metric '{metric}' which is not "
                f"declared in vocabulary.yaml"
            )
    return errors


def check_license(doc: dict) -> list[str]:
    """metadata.license must be in ALLOWED_LICENSES (or absent for default)."""
    md = doc.get("metadata", {})
    lic = md.get("license", "CC-BY-4.0")
    if lic not in ALLOWED_LICENSES:
        return [
            f"metadata.license '{lic}' not in allowed set {sorted(ALLOWED_LICENSES)}"
        ]
    return []


def validate_one(path: Path, schema: dict, vocab: dict) -> list[str]:
    rel = path.relative_to(REPO_ROOT).as_posix()
    errors = []
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]
    if not isinstance(doc, dict):
        return ["root is not a mapping"]

    try:
        jsonschema.validate(doc, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"schema: {e.message} at {list(e.absolute_path)}")

    errors += check_vocabulary(doc, vocab)
    errors += check_license(doc)
    errors += check_path(rel, doc)
    return errors


def discover() -> list[Path]:
    return sorted((REPO_ROOT / "protocols").rglob("protocol.yaml"))


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        targets = [Path(p).resolve() for p in argv[1:]]
    else:
        targets = discover()
    if not targets:
        print("no protocols found")
        return 0

    print(f"loading bundled spec from {SPEC_DIR.relative_to(REPO_ROOT)}/")
    schema, vocab = load_spec()
    print(f"validating {len(targets)} protocol(s)")
    print()

    failed = 0
    for path in targets:
        rel = path.relative_to(REPO_ROOT).as_posix() if path.is_absolute() else str(path)
        errs = validate_one(path, schema, vocab)
        if errs:
            failed += 1
            print(f"✗ {rel}")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"✓ {rel}")

    print()
    if failed:
        print(f"FAIL: {failed}/{len(targets)} protocol(s) have errors")
        return 1
    print(f"PASS: {len(targets)}/{len(targets)} protocol(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
