# OpenCode

Generated file: [`dist/opencode/opencode.json`](../../dist/opencode/opencode.json)

## Install

```bash
mkdir -p ~/.config/opencode
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/opencode/opencode.json \
  -o ~/.config/opencode/opencode.json
```

Per project, drop the same file at `opencode.json` in the repository root.

## Rule format

The `permission` key maps tool names to actions, and for `bash` it maps glob
patterns to actions:

```json
{
  "permission": {
    "bash": {
      "*": "ask",
      "git *": "allow",
      "rm -rf *": "deny"
    }
  }
}
```

Actions are `allow`, `ask` and `deny`. Patterns support `*` for any run of
characters and `?` for exactly one. `~` or `$HOME` at the start of a pattern
expands to the home directory.

Other permission keys OpenCode understands: `read`, `edit`, `glob`, `grep`,
`task`, `skill`, `lsp`, `question`, `webfetch`, `websearch`,
`external_directory`, `doom_loop`. This repo sets `bash`, `read`, `edit` and
`webfetch`.

## Evaluation order: last match wins

This is the important difference from Claude Code, and it is exactly backwards.

Rules are evaluated by pattern match and **the last matching rule wins**. The
generated file is therefore ordered broadest to strictest: the `"*": "ask"`
catch-all comes first, then every allow, then every ask, then every deny last.

If you hand-edit the file, append new deny rules at the bottom. A deny placed
near the top will be overridden by anything below it that also matches.

## Defaults worth knowing

Most permissions default to `allow`. The exceptions are `doom_loop` and
`external_directory`, which default to `ask`, and reading `.env` files, which
defaults to `deny` already.
