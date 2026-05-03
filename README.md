# Hegemonikron Protocols

Public catalog of coaching protocols authored against the
Hegemonikron Spec (bundled in [`spec/`](spec/) in this repo).

Each protocol is a YAML file declaring inputs (against the canonical
metric vocabulary), workflows with cadence + rules, and output
templates. Apps and skills implementing the spec consume protocols
directly from this repo by URL.

## Layout

```
protocols/
└── <author>/
    └── <slug>/
        └── protocol.yaml
```

The path is the public URL slug:
`protocols.cogignition.cloud/<author>/<slug>/` once the rendering
infrastructure is online; until then,
`https://raw.githubusercontent.com/cogignition/protocols/main/protocols/<author>/<slug>/protocol.yaml`
is the canonical fetch URL.

## What's here today

| Author | Slug | Title | License |
|---|---|---|---|
| `cogignition` | [`zone2-fortnight`](protocols/cogignition/zone2-fortnight/protocol.yaml) | Zone 2 Base with Fortnight HRV Gate | CC-BY-4.0 |

This list is maintained manually for v0; auto-generation comes online
with the rendering site.

## Authoring a new protocol

1. Read the spec bundled in this repo at [`spec/`](spec/) —
   especially [`spec/vocabulary.yaml`](spec/vocabulary.yaml) (what
   metrics exist) and [`spec/protocol.schema.json`](spec/protocol.schema.json)
   (what shape your YAML must take).
2. Fork this repo.
3. Create `protocols/<your-handle>/<protocol-slug>/protocol.yaml`. The
   path components MUST match `metadata.author` and `metadata.id` in
   the YAML.
4. Pick a license. Allowed: `CC-BY-4.0` (default), `CC-BY-SA-4.0`,
   `CC0-1.0`, `Apache-2.0`. Anything more restrictive (NC, ND,
   proprietary) will be rejected by CI.
5. Open a PR. CI validates schema, vocabulary references, license,
   and path consistency. See [CONTRIBUTING.md](CONTRIBUTING.md) for
   details.

You don't need to ship rendered HTML or any tooling. Pure YAML is
the contribution.

## Consuming a protocol

In an app or skill:

```bash
curl https://raw.githubusercontent.com/cogignition/protocols/main/protocols/cogignition/zone2-fortnight/protocol.yaml
```

In a runtime, parse the YAML, validate against
[`spec/protocol.schema.json`](spec/protocol.schema.json), then
evaluate workflows by feeding the declared `inputs` through your
configured adapters.

## License

Each protocol's license is declared in its own `metadata.license`
field. The catalog repo itself (this README, the CI configuration,
CONTRIBUTING.md) is licensed CC-BY-4.0; see [`LICENSE`](LICENSE).

## Related

- The Hegemonikron application stack (spec, skills, app) is a
  separate, proprietary product. This catalog is the open piece —
  the schema needed to author against it is bundled here.
