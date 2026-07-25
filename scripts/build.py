#!/usr/bin/env python3
"""Compile rules/*.toml into dist/ for every supported agent.

    python3 scripts/build.py            write dist/ and refresh README tables
    python3 scripts/build.py --check    fail if anything would change

Zero dependencies: tomllib is stdlib on Python 3.11+.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ruleset import DIST_DIR, ROOT, Ecosystem, RuleError, load  # noqa: E402
from targets import claude, codex, cursor, droid, omp, opencode  # noqa: E402

TARGETS = (claude, codex, opencode, omp, droid, cursor)

COVERAGE_START = "<!-- coverage:start -->"
COVERAGE_END = "<!-- coverage:end -->"
BADGES_START = "<!-- badges:start -->"
BADGES_END = "<!-- badges:end -->"

REPO = "josipledic/never-ask-again"


def coverage_table(ecosystems: list[Ecosystem]) -> str:
    rows = [
        "| Ecosystem | What it covers | Allow | Ask | Deny |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    totals = {"allow": 0, "ask": 0, "deny": 0}
    for eco in ecosystems:
        counts = eco.counts()
        for key in totals:
            totals[key] += counts[key]
        rows.append(
            f"| **{eco.name}** | {eco.description} | "
            f"{counts['allow']} | {counts['ask']} | {counts['deny']} |"
        )
    rows.append(
        f"| **Total** | {len(ecosystems)} ecosystems | "
        f"**{totals['allow']}** | **{totals['ask']}** | **{totals['deny']}** |"
    )
    return "\n".join(rows)


def badges(ecosystems: list[Ecosystem]) -> str:
    total = sum(len(eco.rules) for eco in ecosystems)
    shield = "https://img.shields.io/badge"
    return " ".join(
        [
            f"[![CI](https://github.com/{REPO}/actions/workflows/ci.yml/badge.svg)]"
            f"(https://github.com/{REPO}/actions/workflows/ci.yml)",
            f"![rules]({shield}/rules-{total}-2f81f7)",
            f"![agents]({shield}/agents-{len(TARGETS)}-2f81f7)",
            f"![dependencies]({shield}/dependencies-none-2f81f7)",
            f"![license]({shield}/license-MIT-2f81f7)",
        ]
    )


def _splice(text: str, start: str, end: str, body: str) -> str:
    if start not in text or end not in text:
        return text
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    return f"{head}{start}\n\n{body}\n\n{end}{tail}"


def render_readme(ecosystems: list[Ecosystem], current: str) -> str:
    current = _splice(current, BADGES_START, BADGES_END, badges(ecosystems))
    return _splice(current, COVERAGE_START, COVERAGE_END, coverage_table(ecosystems))


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_page(ecosystems: list[Ecosystem], current: str) -> str:
    """Fill the generated regions of the landing page.

    The counts on the page come from the same load() the configs do, so the
    page cannot drift from the rules the way a hand-typed number would.
    """
    totals = {"allow": 0, "ask": 0, "deny": 0}
    for eco in ecosystems:
        for key, value in eco.counts().items():
            totals[key] += value
    total = sum(totals.values())

    chips = [
        f"{total} rules",
        f"{len(ecosystems)} ecosystems",
        f"{len(TARGETS)} agents",
        "0 dependencies",
        "MIT",
    ]
    chips_html = "\n".join(f'      <li class="chip">{c}</li>' for c in chips)

    blurb = {
        "allow": ("#d7d8cc", "Reversible and local."),
        "ask": ("#f2e1d4", "Touches remote state or installs code."),
        "deny": ("#dfd6de", "Destroys, escalates, or exfiltrates."),
    }
    buckets_html = "\n".join(
        f'      <div class="bucket">\n'
        f'        <span class="swatch" style="background:{blurb[k][0]}"></span>\n'
        f'        <div class="k">{k}</div>\n'
        f'        <div class="n">{totals[k]}</div>\n'
        f"        <p>{blurb[k][1]}</p>\n"
        f"      </div>"
        for k in ("allow", "ask", "deny")
    )

    rows = []
    for eco in ecosystems:
        counts = eco.counts()
        rows.append(
            f'      <li><span class="name" title="{_escape(eco.description)}">'
            f'{_escape(eco.name)}</span>'
            f'<span class="num"><b>{counts["allow"]}</b> &middot; '
            f'{counts["ask"]} &middot; {counts["deny"]}</span></li>'
        )
    coverage_html = (
        '    <ul class="cov">\n'
        + "\n".join(rows)
        + "\n    </ul>\n"
        + '    <div class="cov-total"><span class="name">'
        + f"{len(ecosystems)} ecosystems</span>"
        + f'<span class="num">{totals["allow"]} allow &middot; '
        + f'{totals["ask"]} ask &middot; {totals["deny"]} deny</span></div>'
    )

    for start, end, body in (
        ("<!-- gen:chips -->", "<!-- /gen:chips -->", chips_html),
        ("<!-- gen:buckets -->", "<!-- /gen:buckets -->", buckets_html),
        ("<!-- gen:coverage -->", "<!-- /gen:coverage -->", coverage_html),
    ):
        if start in current and end in current:
            head, rest = current.split(start, 1)
            _, tail = rest.split(end, 1)
            current = f"{head}{start}\n{body}\n{end}{tail}"
    return current


def outputs(ecosystems: list[Ecosystem]) -> dict[Path, str]:
    files: dict[Path, str] = {
        DIST_DIR / target.PATH: target.render(ecosystems) for target in TARGETS
    }
    readme = ROOT / "README.md"
    if readme.exists():
        files[readme] = render_readme(ecosystems, readme.read_text())
    page = ROOT / "docs/index.html"
    if page.exists():
        files[page] = render_page(ecosystems, page.read_text())
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if any generated file is out of date",
    )
    args = parser.parse_args()

    try:
        ecosystems = load()
    except RuleError as error:
        print(f"rules error: {error}", file=sys.stderr)
        return 2

    stale: list[Path] = []
    for path, content in outputs(ecosystems).items():
        existing = path.read_text() if path.exists() else None
        if existing == content:
            continue
        stale.append(path)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    total = sum(len(eco.rules) for eco in ecosystems)
    if args.check:
        if stale:
            print("out of date, run python3 scripts/build.py:", file=sys.stderr)
            for path in stale:
                print(f"  {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print(f"dist/ is up to date ({total} rules)")
        return 0

    for path in stale:
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"{total} rules across {len(ecosystems)} ecosystems -> {len(TARGETS)} agents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
