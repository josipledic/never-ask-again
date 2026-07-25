# Claude Code

Generated file: [`dist/claude/settings.json`](../../dist/claude/settings.json)

## Install

```bash
# global, every project
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/claude/settings.json \
  -o ~/.claude/settings.json

# or per project, committed and shared with the team
mkdir -p .claude && cp dist/claude/settings.json .claude/settings.json

# or per project, personal and gitignored
mkdir -p .claude && cp dist/claude/settings.json .claude/settings.local.json
```

Run `/permissions` in a session to see every active rule and which file it came
from.

## Rule format

`Tool` or `Tool(specifier)`. A bare `Bash` matches everything, and as a deny
rule it removes the tool from the model's context entirely.

For Bash the specifier is a command pattern. A trailing ` *` enforces a word
boundary, so the prefix must be followed by a space or by end-of-string.
`Bash(ls *)` matches `ls -la` and bare `ls`, but not `lsof`. Wildcards work at
any position.

`Bash(command:rm *)` style parameter rules are ignored with a startup warning.
Use `Bash(rm *)`.

## Evaluation order

Deny, then ask, then allow. First match wins, and specificity does not break
ties, which is why [a broad deny cannot carry exceptions](../gotchas.md#3-a-broad-deny-cannot-carry-exceptions).

Compound commands are evaluated per subcommand. The separators are `&&`, `||`,
`;`, `|`, `|&`, `&` and newlines.

## Settings precedence

Highest first: managed settings, CLI arguments, `.claude/settings.local.json`,
`.claude/settings.json`, `~/.claude/settings.json`. A deny at any level wins
everywhere.

Allow rules in a committed project `settings.json` only apply after the
workspace trust dialog is accepted. Deny and ask apply immediately.

## File rules

`Read` and `Edit` rules use gitignore pattern syntax:

| Form | Means |
| --- | --- |
| `//path` | filesystem absolute |
| `~/path` | home directory |
| `/path` | anchored to the settings file's own location |
| `path` | relative to the working directory |

A `Read` deny also blocks `Edit` on the same path. `Write(...)` and `Glob(...)`
rules are accepted but never matched, so this repo emits `Edit(...)` and
`Read(...)` instead, and `validate.py` fails on anything else.

## Notes on this ruleset

`defaultMode` is set to `acceptEdits`. File edits inside the working directory
go through without a prompt, which is the point of pairing edit acceptance with
a tight Bash allowlist.

Choosing "Yes, don't ask again" during a session writes the rule to
`.claude/settings.local.json` at the git repository root. That is the intended
way to grow this list: keep the deny block, keep the sections for your stack,
and promote the local additions into your global file every few weeks.
