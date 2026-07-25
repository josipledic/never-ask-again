# Contributing

Two kinds of contribution are useful here: rules for a stack that is missing,
and adapters for an agent that is missing.

## Setup

None. Python 3.11 or newer, standard library only.

```bash
python3 scripts/build.py       # regenerate dist/ and the README tables
python3 scripts/validate.py    # run every invariant
```

If you have `codex` installed, `validate.py` additionally runs every test
fixture through the real `codex execpolicy` binary.

## Adding rules

Edit the relevant file in `rules/`, or add a new one. Each file is one
ecosystem and needs `name`, `slug`, `description` and `order` at the top.

Rules are grouped by shared rationale:

```toml
[[group]]
decision = "allow"
why = "Lockfile-exact installs. The dependency graph is already decided."
exact = ["npm ci", "pnpm install --frozen-lockfile"]
not_match = ["npm install express"]
```

`cmds` entries get a trailing ` *`, which matches the bare command and the
command with any arguments. `exact` entries match only the literal string.

### What goes in which bucket

```
allow = reversible and local
ask   = touches remote state or installs code
deny  = destroys, escalates, or exfiltrates
```

Some consequences of applying that consistently, which reviewers will hold you
to:

- Anything wrapper-shaped names the inner command. `npx tsc`, never `npx`.
- Lockfile-exact installs are allow. Plain `install` and `add` are ask, because
  lifecycle scripts are remote code execution.
- Cloud CLIs allow read verbs and deny specific mutating verbs. Never a blanket
  deny on the binary, because a deny cannot carry exceptions.
- Publishing to any registry is deny. There is no undo for a published version.
- Task runners are allowed for conventional target names only, never with a
  bare wildcard, because a target can be added in the same session.

### Test fixtures

Add at least one `match` to any group you introduce, and a `not_match` wherever
a nearby rule could plausibly swallow it. These are not decoration: CI runs
them through a simulation of Claude Code's evaluation order and fails on a
wrong answer.

## Adding an agent

See [AGENTS.md](AGENTS.md). The short version: one module under
`scripts/targets/`, registered in `scripts/build.py`, plus a page under
`docs/agents/`.

Cite the agent's documentation for its matching semantics in the module
docstring, especially the order in which rules are evaluated. Three of the six
agents supported so far disagree about that, and getting it wrong inverts allow
and deny.

## Before opening a PR

```bash
python3 scripts/build.py
python3 scripts/validate.py
git add rules dist README.md
```

The regenerated `dist/` must be part of the commit. CI checks that a fresh
build produces exactly what is committed.

## Style

No em-dashes. One sentence per `why`, saying why the decision is what it is.
