# Bob

Generated file: [`dist/bob/settings.json`](../../dist/bob/settings.json)

Bob is the IBM Bob IDE VS Code extension.

## Install

```bash
mkdir -p ~/.bob/settings
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/bob/settings.json \
  -o ~/.bob/settings/settings.json
```

If `~/.bob/settings/settings.json` already exists, merge rather than overwrite:
read the existing file, union the `approvedCommands` arrays, and keep every
other key untouched. See the merge rules below.

## Rule format

```json
{
  "approval": {
    "allowedExecutors": [
      {
        "toolId": "execute_command",
        "approvedCommands": ["git status", "go test"],
        "deniedCommands": []
      }
    ]
  }
}
```

`approvedCommands` is a prefix allowlist for the `execute_command` tool. Bob
matches an entry if the command string starts with it, so `"go test"` covers
`"go test ./..."` and any other flags. Commands not in the list prompt.
`deniedCommands` is left empty: the allowlist is the restriction.

## What this repo generates

Bob's permission model has no deny list in the config, so only `allow` rules
map onto an entry:

- `allow` rules become entries in `approval.allowedExecutors[0].approvedCommands`
- `ask` and `deny` rules are **not** emitted, so those commands prompt

Commands with an embedded wildcard (`*`) are dropped rather than guessed at,
since Bob matches on plain string prefixes, not glob patterns.

## Merge rules

When merging with an existing config:

- `approvedCommands`: union, drop duplicates
- `deniedCommands`: union (adding denies is always safe)
- Leave every other key in the file untouched

## Verify the matching behaviour yourself

Bob matches `approvedCommands` entries as prefix matches against the full
command string. Confirm that against your installed version before relying on
it. If your build matches whole strings only, the allowlist will do less than
expected rather than more, so the failure mode is extra prompts, not extra
permissions.
