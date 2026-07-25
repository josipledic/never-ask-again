# Droid

Generated file: [`dist/droid/settings.json`](../../dist/droid/settings.json)

Droid is Factory's CLI, `droid`.

## Install

```bash
mkdir -p ~/.factory
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/droid/settings.json \
  -o ~/.factory/settings.json
```

On Windows the path is `%USERPROFILE%\.factory\settings.json`. Local overrides
go in `settings.local.json` beside it.

## Rule format

```json
{
  "sessionDefaultSettings": { "autonomyLevel": "medium" },
  "commandAllowlist": ["ls", "pwd"],
  "commandBlocklist": ["shutdown", "mkfs"]
}
```

`commandAllowlist` runs without confirmation. `commandBlocklist` can never run
regardless of approvals. Anything unlisted follows the session autonomy level,
which is `off`, `low`, `medium` or `high`.

There is a third key, `commandDenylist`, for commands that require explicit
approval.

## What this repo generates

There are only two tiers here that map cleanly, so:

- `allow` rules become `commandAllowlist`
- `deny` rules become `commandBlocklist`
- `ask` rules are deliberately **not** emitted, so they fall through to the
  autonomy level and prompt

`autonomyLevel` is set to `medium`, which is the level at which the allowlist
does useful work without the unlisted commands running unattended.

## Known gap: no wildcards

Entries are plain command strings. Any rule in this repo with an embedded
wildcard, such as `aws * describe-*`, is dropped rather than guessed at, which
leaves those commands prompting. That thins out the cloud CLI coverage
considerably.

## Verify the matching behaviour yourself

Factory's documentation describes these as command lists without stating
whether entries are matched as prefixes or as whole strings. This repo emits
prefixes, on the assumption that `git` in the allowlist covers `git status`.

Confirm that against your installed version before relying on it. If your build
matches whole strings instead, the allowlist will simply do less than expected
rather than more, so the failure mode is extra prompts, not extra permissions.

## Subagents

`subagentAutonomyLevel` controls what spawned agents inherit, and both it and
the session level are clamped by an org-managed `maxAutonomyLevel`. This repo
denies the agent binaries themselves, including `droid`, so a nested agent
cannot start with a different permission set.
