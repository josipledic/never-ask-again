# Cursor CLI

Generated file: [`dist/cursor/cli-config.json`](../../dist/cursor/cli-config.json)

## Install

```bash
mkdir -p ~/.cursor
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/cursor/cli-config.json \
  -o ~/.cursor/cli-config.json
```

Per project, the same shape goes in `.cursor/cli.json`. Note that granting a
permission interactively has been reported to write to the global file even
when a project file exists, so check which one actually changed.

## Rule format

```json
{
  "permissions": {
    "allow": ["Shell(ls)", "Shell(git)", "Read(src/**/*.ts)"],
    "deny": ["Shell(rm)", "Read(.env*)"]
  }
}
```

Token types are `Shell(commandBase)`, `Read(pathOrGlob)`,
`Write(pathOrGlob)`, `WebFetch(domainOrPattern)` and `Mcp(server:tool)`.
Deny beats allow.

## The important limitation: first token only

`Shell()` matches **the first token of the command line**. `Shell(git)` means
every git subcommand. There is no way to write `Shell(git push --force)` and
have it mean something narrower than `Shell(git)`.

That is incompatible with how this repo works, since almost every ecosystem
here allows some subcommands of a binary and denies others. The generator
therefore degrades conservatively:

| Every rule under a base is | Result |
| --- | --- |
| allow | `Shell(base)` goes in `allow` |
| deny | `Shell(base)` goes in `deny` |
| mixed | omitted entirely, so it prompts |

65 command bases end up in that third row, including `git`, `docker`,
`kubectl`, `aws`, `terraform`, `gh` and `npm`. They are listed in the `_note`
field of the generated file.

So this target is coarser than the other five by construction. What it gives
you is silence on the unambiguous cases, `rg`, `jq`, `tsc`, `pytest`,
`cargo build` and the like, and a hard deny on the unambiguously destructive
ones. The interesting middle keeps prompting.

## Worth checking

Cursor's documentation shows a `Shell(curl:*)` form, which suggests argument
patterns may be supported after all. If that turns out to work in your version,
the degradation above is unnecessary and the adapter in
`scripts/targets/cursor.py` should be rewritten to emit full patterns. That
would be a welcome PR.

## Auto-review

Cursor 3.6 added an auto-review run mode configured through
`.cursor/permissions.json` with `allow_instructions` and `block_instructions`.
That is a separate mechanism from the token list above and this repo does not
generate it.
