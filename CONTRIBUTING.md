# Contributing a protocol

Protocols are pure YAML files validated by CI against the bundled
Hegemonikron Spec schemas under [`spec/`](spec/) in this repo.
No code, no tooling, no rendering — just YAML.

## Workflow

1. Fork this repo.
2. Create a directory: `protocols/<your-handle>/<protocol-slug>/`.
   - `<your-handle>` should be your stable author identifier, lowercase,
     dash-separated (e.g., `cogignition`, `acme-coaching`).
   - `<protocol-slug>` should be lowercase, dash-separated
     (e.g., `zone2-fortnight`, `marathon-base-12wk`).
3. Add `protocol.yaml` inside that directory.
4. Open a PR with the title `Add <author>/<slug>` (or
   `Update <author>/<slug>` for revisions).

## What CI checks

Every push and PR runs `.github/workflows/validate.yml`, which:

1. **Schema:** validates each `protocol.yaml` against
   [`spec/protocol.schema.json`](spec/protocol.schema.json) bundled
   in this repo.
2. **Vocabulary:** every `inputs[*].metric` must exist in
   [`spec/vocabulary.yaml`](spec/vocabulary.yaml).
3. **License:** `metadata.license` must be one of:
   - `CC-BY-4.0` (default; recommended)
   - `CC-BY-SA-4.0` (share-alike)
   - `CC0-1.0` (public domain dedication)
   - `Apache-2.0` (with patent grant)
   Anything else (NC, ND, proprietary) will be rejected.
4. **Path consistency:** the file path must match the YAML metadata.
   `protocols/<author>/<slug>/protocol.yaml` must have
   `metadata.author == <author>` and `metadata.id == <slug>`.

If any check fails, the PR will not be merged. Fix locally, push, CI
re-runs.

## Local validation

Before pushing, you can run the same checks locally:

```bash
pip install pyyaml jsonschema requests
python tools/validate.py protocols/<your-handle>/<your-slug>/protocol.yaml
```

(`tools/validate.py` is a thin local wrapper around the same logic CI
uses; it's checked in for offline development.)

## Authoring tips

- **Speak the canonical vocabulary.** Don't invent metric names.
  If a metric you need isn't in the spec, propose its addition there
  *first*; once it lands, your protocol can reference it.
- **Reference research.** `metadata.references` is a list of URLs.
  Cite the papers, posts, or coaches your protocol is built on.
- **Write your output style narrowly.** `output.style` is the
  prompt scaffold the runtime's edge model receives. Vague styles
  produce vague briefs. "Morning brief, 3 sentences, no filler" is
  a tighter contract than "morning summary."
- **Test against the mock adapter.** When `cogignition/hegemonikron`
  ships, you'll be able to evaluate your protocol against synthetic
  data without wiring up real sensors. For now, structural
  validation is the most rigorous check available.

## License of the catalog

The catalog itself (this file, the README, CI config, etc.) is
CC-BY-4.0. Individual protocols declare their own license; see the
allowed list above. Forking a protocol creates a new file in your
own author namespace; the original retains its license, your
derivative may choose any of the allowed licenses (subject to
share-alike if the original was CC-BY-SA-4.0).

## Code of conduct

Coaching protocols are inherently opinionated. Disagreement about
philosophy, modality, or methodology is welcome — but it lives in
your own protocol, not in PRs against someone else's. Don't open
PRs to "fix" someone else's protocol unless they explicitly invited
collaborators in the description.
