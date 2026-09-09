# Bob

Generated file: [`dist/bob/settings.json`](../../dist/bob/settings.json)

Bob is the IBM Bob IDE VS Code extension.

## Install

```bash
mkdir -p ~/.bob
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/bob/settings.json \
  -o ~/.bob/settings.json
```

Per project, drop the same file at `.bob/settings.json` in the repository root.
The project-level file takes precedence over the user-level one.

## Rule format

```json
{
  "autoApprove": {
    "read": true,
    "edit": true,
    "execute": false,
    "allowedCommands": ["git status", "go test"],
    "mcp": false
  }
}
```

`allowedCommands` is a flat allowlist. Bob matches entries as prefix/substring
against the full command string. A command not in the list prompts when
`execute` is false. There is no separate deny list in the config - unlisted
commands simply prompt.

## What this repo generates

Bob's permission model has no deny list, so only `allow` rules map onto a
config entry:

- `allow` rules become entries in `autoApprove.allowedCommands`
- `ask` and `deny` rules are **not** emitted, so those commands prompt

`execute` is set to `false` so the allowlist does the work. Commands with an
embedded wildcard (`*`) are dropped rather than guessed at, since Bob matches
on plain strings, not glob patterns.

## Merge rules

When merging with an existing config:

- `allowedCommands`: union, drop duplicates
- Boolean flags (`read`, `edit`, `execute`, `mcp`): keep the more restrictive
  value (`false` beats `true`)

## Verify the matching behaviour yourself

Bob's documentation describes `allowedCommands` entries as prefix/substring
matches against the full command string. Confirm that against your installed
version before relying on it. If your build matches whole strings only, the
allowlist will do less than expected rather than more, so the failure mode is
extra prompts, not extra permissions.
