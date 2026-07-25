# Codex

Generated file: [`dist/codex/default.rules`](../../dist/codex/default.rules)

## Install

```bash
mkdir -p ~/.codex/rules
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/codex/default.rules \
  -o ~/.codex/rules/default.rules
```

In `~/.codex/config.toml`:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

## Rule format

Starlark. `prefix_rule(pattern, decision, justification, match, not_match)`
where `pattern` is an argv list and a nested list is a union of alternatives at
that position:

```python
prefix_rule(
    pattern = ["git", ["add", "commit", "switch", "fetch"]],
    decision = "allow",
    justification = "Local and reversible.",
)
```

`decision` is `allow`, `prompt` or `forbidden`, defaulting to `allow`. The most
restrictive match wins, so ordering in the file does not matter.

This repo's three buckets map to `allow`, `prompt` and `forbidden`.

## Verify anything before trusting it

```bash
codex execpolicy check --pretty --rules ~/.codex/rules/default.rules -- git push --force
```

`scripts/validate.py` runs every test fixture in `rules/*.toml` through this
binary when it is installed, and fails if a decision comes back inverted.

## Known gap: no wildcards

Codex matches literal argv prefixes. It has no equivalent of
`Bash(aws * describe-* *)`, so rules with an embedded wildcard cannot be
expressed at all.

Rather than dropping them silently, the generator emits them as comments:

```python
# not expressible in Codex (embedded wildcard): aws * describe-* *
```

Those commands fall through to your `approval_policy`, which means they prompt
under `on-request`. The practical effect is that the cloud CLI sections are
much thinner here than in the other targets. Grep the generated file for
`not expressible` to see the full list.

## Compound commands

Codex splits `bash -lc` scripts with tree-sitter when the script is a linear
chain of plain words joined by `&&`, `||`, `;` or `|`. With redirection,
substitution, environment assignment, globs or control flow it does not split,
and evaluates the whole string as a single invocation.

## Sandboxing is separate

Rules control commands. The sandbox controls the filesystem and network, and is
configured independently in `~/.codex/config.toml` through `sandbox_mode`
(`read-only`, `workspace-write`, `danger-full-access`) and
`sandbox_workspace_write.writable_roots`. Use both.

Rules are still marked experimental in the Codex documentation, so re-check
after upgrades.
