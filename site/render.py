#!/usr/bin/env python3
"""Render the Hegemonikron protocol catalog to static HTML.

Walks `protocols/<author>/<slug>/protocol.yaml`, emits a per-protocol
detail page at `dist/<author>/<slug>/index.html`, plus an index page
at `dist/index.html` listing every protocol grouped by author.

Style mirrors blog.cogignition.cloud's dark editorial system: same
palette, fonts, kicker bars, coral accents. The CSS is lifted
verbatim from blog/public/assets/site.css; component classes are
reused unchanged so the catalog feels like a sibling of the blog.

Run from the repo root:

    python3 site/render.py            # writes dist/
    python3 site/render.py --serve    # also boots a local server on :8000
"""

from __future__ import annotations

import argparse
import html
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml not installed. Run: pip install pyyaml")


REPO_ROOT = Path(__file__).resolve().parent.parent
PROTOCOLS_DIR = REPO_ROOT / "protocols"
SITE_DIR = REPO_ROOT / "site"
ASSETS_DIR = SITE_DIR / "assets"
DIST_DIR = REPO_ROOT / "dist"

CSS_VERSION = 1   # bump when assets/site.css changes


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

@dataclass
class Protocol:
    author: str
    slug: str
    path: Path
    raw: dict

    @property
    def metadata(self) -> dict:
        return self.raw.get("metadata", {})

    @property
    def title(self) -> str:
        return self.metadata.get("title", self.slug)

    @property
    def description(self) -> str:
        return (self.metadata.get("description", "") or "").strip()

    @property
    def license(self) -> str:
        return self.metadata.get("license", "CC-BY-4.0")

    @property
    def version(self) -> str:
        return str(self.metadata.get("version", ""))

    @property
    def created(self) -> str:
        return str(self.metadata.get("created", ""))

    @property
    def references(self) -> list[str]:
        return list(self.metadata.get("references", []) or [])

    @property
    def inputs(self) -> dict:
        return self.raw.get("inputs", {}) or {}

    @property
    def workflows(self) -> dict:
        return self.raw.get("workflows", {}) or {}

    @property
    def url_path(self) -> str:
        return f"/{self.author}/{self.slug}/"

    @property
    def yaml_url(self) -> str:
        return f"/{self.author}/{self.slug}/protocol.yaml"


def discover() -> list[Protocol]:
    out: list[Protocol] = []
    for path in sorted(PROTOCOLS_DIR.rglob("protocol.yaml")):
        rel = path.relative_to(PROTOCOLS_DIR).parts
        if len(rel) != 3 or rel[2] != "protocol.yaml":
            continue
        author, slug, _ = rel
        with path.open() as f:
            raw = yaml.safe_load(f) or {}
        out.append(Protocol(author=author, slug=slug, path=path, raw=raw))
    return out


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def page_chrome(title: str, *, depth: int = 0) -> str:
    """Render head + nav. `depth` is how many directories deep this
    page is from the dist root, so we can emit working *relative*
    asset paths (project Pages sites live at `username.github.io/repo/`,
    so `/assets/...` resolves to the wrong place; relative paths work
    on both the project URL and the custom domain)."""
    rel = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(title)}</title>
<link rel="stylesheet" href="{rel}assets/site.css?v={CSS_VERSION}" />
<meta property="og:title" content="{esc(title)}" />
<meta property="og:image" content="{rel}assets/og-default.png?v={CSS_VERSION}" />
<meta name="twitter:card" content="summary_large_image" />
</head>
<body>
<header class="site-nav">
  <a class="brand" href="{rel or './'}">cogignition<span class="dot">.</span>protocols</a>
  <nav>
    <a href="{rel or './'}">catalog</a>
    <a href="https://github.com/cogignition/hegemonikron-spec">spec</a>
    <a href="https://github.com/cogignition/protocols">github</a>
  </nav>
</header>
"""


def page_footer() -> str:
    year = datetime.now(timezone.utc).year
    return f"""<footer class="site-foot">
  <span>cogignition / protocols · {year}</span>
  <span>cc-by-4.0 unless noted</span>
</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Detail page
# ---------------------------------------------------------------------------

def render_detail(p: Protocol) -> str:
    inputs_rows = "\n".join(render_input_row(name, spec) for name, spec in p.inputs.items())
    workflows_blocks = "\n".join(render_workflow(name, wf) for name, wf in p.workflows.items())
    refs = ""
    if p.references:
        items = "\n".join(f'    <li><a href="{esc(r)}">{esc(r)}</a></li>' for r in p.references)
        refs = f"""
<section class="page-section">
  <h2>References</h2>
  <ul class="ref-list">
{items}
  </ul>
</section>
"""

    return f"""{page_chrome(f"{p.title} · {p.author}", depth=2)}
<main class="page protocol-detail">
  <p class="crumb"><a href="../../">catalog</a> &nbsp;/&nbsp; {esc(p.author)} &nbsp;/&nbsp; <span>{esc(p.slug)}</span></p>

  <p class="kicker-bar">protocol · {esc(p.author)}</p>
  <h1 class="masthead">{esc(p.title)}</h1>
  <p class="deck">{esc(p.description) if p.description else "&nbsp;"}</p>

  <dl class="meta-grid">
    <dt>id</dt>           <dd><code>{esc(p.slug)}</code></dd>
    <dt>author</dt>       <dd><code>{esc(p.author)}</code></dd>
    <dt>license</dt>      <dd>{esc(p.license)}</dd>
    {(f'<dt>version</dt><dd>{esc(p.version)}</dd>' if p.version else '')}
    {(f'<dt>created</dt><dd>{esc(p.created)}</dd>' if p.created else '')}
    <dt>raw</dt>          <dd><a href="protocol.yaml">protocol.yaml</a></dd>
  </dl>

  <section class="page-section">
    <div class="section-head"><h2>Inputs</h2><span class="lede">{len(p.inputs)} declared</span></div>
    <table class="inputs-table">
      <thead><tr><th>Name</th><th>Metric</th><th>Aggregation</th><th>Window</th></tr></thead>
      <tbody>
{inputs_rows}
      </tbody>
    </table>
  </section>

  <section class="page-section">
    <div class="section-head"><h2>Workflows</h2><span class="lede">{len(p.workflows)} declared</span></div>
{workflows_blocks}
  </section>

  {refs}
</main>
{page_footer()}"""


def render_input_row(name: str, spec: dict) -> str:
    spec = spec or {}
    return (
        "        <tr>"
        f"<td><code>{esc(name)}</code></td>"
        f"<td>{esc(spec.get('metric', ''))}</td>"
        f"<td>{esc(spec.get('aggregation', 'latest'))}</td>"
        f"<td>{esc(spec.get('window', '—'))}</td>"
        "</tr>"
    )


def render_workflow(name: str, wf: dict) -> str:
    wf = wf or {}
    cadence = wf.get("cadence", "")
    inputs = wf.get("inputs", []) or []
    rules = wf.get("rules", []) or []
    output = wf.get("output", {}) or {}

    rules_html = ""
    if rules:
        rules_html = "<ol class=\"rule-list\">\n"
        for r in rules:
            if "if" in r:
                cond = esc(r.get("if", ""))
                then = esc_payload(r.get("then", {}))
                rules_html += (
                    f'    <li><span class="rule-when">if</span> '
                    f'<code>{cond}</code> '
                    f'<span class="rule-then">then</span> {then}</li>\n'
                )
            elif "else" in r:
                else_ = esc_payload(r.get("else", {}))
                rules_html += f'    <li><span class="rule-else">else</span> {else_}</li>\n'
        rules_html += "</ol>"

    output_html = ""
    if output:
        style = output.get("style", "")
        mention = output.get("mention", []) or []
        output_html = "<div class=\"workflow-output\">"
        if style:
            output_html += f'<p><span class="lbl">style</span> {esc(style)}</p>'
        if mention:
            tags = " ".join(f'<code>{esc(m)}</code>' for m in mention)
            output_html += f'<p><span class="lbl">mention</span> {tags}</p>'
        output_html += "</div>"

    inputs_html = ""
    if inputs:
        inputs_html = (
            '<p class="workflow-inputs"><span class="lbl">inputs</span> '
            + " ".join(f'<code>{esc(i)}</code>' for i in inputs)
            + "</p>"
        )

    return f"""<article class="workflow">
  <header class="workflow-head">
    <h3>{esc(name)}</h3>
    <code class="cadence">{esc(cadence)}</code>
  </header>
  {inputs_html}
  {rules_html}
  {output_html}
</article>
"""


def esc_payload(payload) -> str:
    """Render a rule's then/else payload as inline tags."""
    if isinstance(payload, dict):
        if not payload:
            return "<em>—</em>"
        return " ".join(
            f'<span class="kv"><span class="k">{esc(k)}</span>=<span class="v">{esc(v)}</span></span>'
            for k, v in payload.items()
        )
    return esc(str(payload))


# ---------------------------------------------------------------------------
# Index page
# ---------------------------------------------------------------------------

def render_index(protocols: list[Protocol]) -> str:
    by_author: dict[str, list[Protocol]] = {}
    for p in protocols:
        by_author.setdefault(p.author, []).append(p)

    sections = ""
    for author in sorted(by_author):
        items = "\n".join(render_index_card(p) for p in sorted(by_author[author], key=lambda x: x.slug))
        sections += f"""
<section class="page-section">
  <div class="section-head">
    <h2>{esc(author)}</h2>
    <span class="lede">{len(by_author[author])} protocol{"s" if len(by_author[author]) != 1 else ""}</span>
  </div>
  <div class="cards">
{items}
  </div>
</section>
"""

    return f"""{page_chrome("Protocols · cogignition", depth=0)}
<main class="page">
  <p class="kicker-bar">cogignition / protocols</p>
  <h1 class="masthead">A catalog of <em>coaching protocols.</em></h1>
  <p class="deck">YAML-authored, schema-validated, and forkable. Anyone implementing the
  <a href="https://github.com/cogignition/hegemonikron-spec">Hegemonikron spec</a> can consume these directly.</p>

{sections}

  <section class="page-section">
    <div class="section-head"><h2>Author your own</h2></div>
    <p>Fork <a href="https://github.com/cogignition/protocols"><code>cogignition/protocols</code></a>,
    drop a <code>protocol.yaml</code> at <code>protocols/&lt;your-handle&gt;/&lt;slug&gt;/</code>,
    open a PR. CI validates schema, vocabulary references, license, and path consistency.
    Merged PRs auto-deploy to this site within a minute.</p>
  </section>
</main>
{page_footer()}"""


def render_index_card(p: Protocol) -> str:
    summary = (p.description or "").split("\n\n")[0][:280]
    rel_path = f"{p.author}/{p.slug}/"
    return f"""<div class="card">
  <a class="card-link" href="{esc(rel_path)}">
    <div class="card-body">
      <div class="card-meta">
        <span class="card-date">{esc(p.author)} / {esc(p.slug)}</span>
        <span class="card-tag">{esc(p.license)}</span>
      </div>
      <h3 class="card-title">{esc(p.title)}</h3>
      <p class="card-summary">{esc(summary)}</p>
    </div>
  </a>
</div>"""


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_dist(protocols: list[Protocol]) -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    # Copy assets
    out_assets = DIST_DIR / "assets"
    out_assets.mkdir()
    for f in ASSETS_DIR.iterdir():
        if f.is_file():
            shutil.copy2(f, out_assets / f.name)

    # CNAME
    cname = REPO_ROOT / "CNAME"
    if cname.exists():
        shutil.copy2(cname, DIST_DIR / "CNAME")

    # Index
    (DIST_DIR / "index.html").write_text(render_index(protocols))

    # Per-protocol pages + raw YAML
    for p in protocols:
        out = DIST_DIR / p.author / p.slug
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(render_detail(p))
        shutil.copy2(p.path, out / "protocol.yaml")

    print(f"Wrote {len(protocols)} protocol(s) to {DIST_DIR}")


def maybe_serve():
    import http.server, socketserver, os
    os.chdir(DIST_DIR)
    port = 8000
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"Serving {DIST_DIR} at http://localhost:{port} (Ctrl-C to stop)")
        httpd.serve_forever()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="boot a local HTTP server on :8000 after rendering")
    args = parser.parse_args(argv)

    protocols = discover()
    if not protocols:
        print("no protocols found in protocols/", file=sys.stderr)
        return 1
    write_dist(protocols)

    if args.serve:
        maybe_serve()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
