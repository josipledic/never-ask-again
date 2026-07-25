# Working in this repository

Read this before editing anything here.

## The one rule

`rules/*.toml` is the only hand-maintained source. Everything in `dist/` is
generated. If you edit a file under `dist/` your change will be silently
reverted by the next build, and CI will fail on the drift check first.

```
rules/*.toml  ->  scripts/build.py  ->  dist/<agent>/
```

## After any change to rules/

```bash
python3 scripts/build.py
python3 scripts/validate.py
```

Commit the regenerated `dist/` alongside the rules change. CI runs
`build.py --check`, which fails if the two disagree.

## Adding a rule

Find the ecosystem file, then either add the command to an existing group whose
`why` already fits, or add a new group. Do not add a group whose `why`
duplicates one already in the file.

```toml
[[group]]
decision = "allow"          # allow | ask | deny
why = "One sentence, present tense, saying why this decision and not another."
cmds = ["tool subcommand"]  # a trailing " *" is added, so args are covered
exact = ["tool --version"]  # no trailing wildcard, matches only this command
match = ["tool subcommand --flag"]      # CI asserts this resolves to `decision`
not_match = ["tool other-subcommand"]   # CI asserts this does not
```

Three things the validator will reject:

- A `cmds` entry that stops at a wrapper, such as `npx` or `docker exec`, in an
  allow group. Name the inner command.
- A rule that a higher-precedence rule already swallows. Order is deny, then
  ask, then allow, and specificity does not break ties, so an allow for
  `kubectl apply --dry-run=client` is dead if `kubectl apply` is denied.
- A duplicate of a rule defined in another ecosystem file.

## Adding an agent

Write `scripts/targets/<agent>.py` exposing `PATH`, `CONFIG_PATH` and
`render(ecosystems) -> str`, then add it to `TARGETS` in `scripts/build.py`.

Get the target's matching semantics from its own documentation before you
write the adapter, and put what you found in the module docstring. The order in
which rules are evaluated differs between every agent supported so far, and
getting it backwards inverts allow and deny.

Also add `docs/agents/<agent>.md` and a row in the README table.

## House style

- No em-dashes anywhere. Plain hyphens, commas, parentheses, colons, periods.
- Rationales in `why` are one sentence, and say why the decision is what it is
  rather than restating the command.
- Prefer being specific about a real consequence over hedging.
