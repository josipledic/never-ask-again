# Installing never-ask-again

You are an AI coding agent and someone has pointed you at this file so you can
configure your own permission rules. Follow it exactly.

Repository: <https://github.com/josipledic/never-ask-again>
Raw file base: `https://raw.githubusercontent.com/josipledic/never-ask-again/main/`

## Before anything else

Three rules govern this whole procedure.

**1. Adding an allow rule is a privilege grant to yourself.** You are editing
the file that decides what you are permitted to do. Apply the `deny` block on
your own if you like, since it only ever narrows what you can do. For `allow`
and `ask` rules, show the human the diff and wait for them to say yes. Do not
treat their original "install this" as consent for that step. It is not.

**2. Merge, never overwrite.** Read the existing config first. If the user
already has rules, keep every one of them. Never delete an existing `deny`
entry, even if this repo does not have it, and even if it looks redundant.

**3. Change nothing else.** These config files hold model settings, API keys,
MCP servers and hooks. Touch the permission keys named below and leave every
other key exactly as you found it.

If you cannot satisfy all three, stop and tell the user what you would need.

## Step 1: identify yourself

| If you are | Fetch | Write to | Config key |
| --- | --- | --- | --- |
| Bob | `dist/bob/settings.json` | `~/.bob/settings/settings.json` | `approval` |
| Claude Code | `dist/claude/settings.json` | `~/.claude/settings.json` | `permissions` |
| Codex | `dist/codex/default.rules` | `~/.codex/rules/default.rules` | whole file |
| OpenCode | `dist/opencode/opencode.json` | `~/.config/opencode/opencode.json` | `permission` |
| Oh My Pi | `dist/omp/config.yml` | `~/.omp/agent/config.yml` | `bash.patterns`, `tools` |
| Droid | `dist/droid/settings.json` | `~/.factory/settings.json` | `commandAllowlist`, `commandBlocklist` |
| Cursor CLI | `dist/cursor/cli-config.json` | `~/.cursor/cli-config.json` | `permissions` |

If you are none of these, say so and stop. Do not improvise a format for an
agent that is not on the list. Point the user at
[CONTRIBUTING.md](CONTRIBUTING.md), which explains how to add a target.

## Step 2: read what is already there

Read the destination file. If it does not exist, note that and treat the
existing rule set as empty. If it exists but does not parse, stop and tell the
user; do not repair it silently.

Record what is already configured, so you can report the merge accurately.

## Step 3: merge

Fetch the file from the table above and combine it with what you found.

- Union the rule lists. Order matters differently per agent, so keep the
  incoming file's relative ordering for incoming rules, and preserve the user's
  existing entries in their existing positions.
- Drop exact duplicates.
- On conflict, where the user's config and this repo disagree about the same
  command, keep the more restrictive of the two and list the conflict in your
  report.
- Leave every non-permission key untouched.

For Bob, merge `approval.allowedExecutors[0].approvedCommands` as a union
(drop duplicates). Merge `approval.allowedExecutors[0].deniedCommands` as a
union too (adding denies is always safe). Leave every other key in the file
untouched.

For Codex the destination is a standalone rules file rather than a key inside a
larger config, so a merge only applies if `~/.codex/rules/default.rules`
already exists. If it does, append the new `prefix_rule` entries and tell the
user which ones you added.

## Step 4: show the diff and stop

Print a summary before writing anything:

```
deny    +N rules   (safe to apply, narrows what I can do)
ask     +N rules
allow   +N rules   (this widens what I can run without asking)
kept    N of your existing rules
conflicts: <list, or none>
```

Then show the actual `allow` entries you are proposing to add, or a
representative sample with an exact count if the list is long. Ask the user to
confirm.

If they approve only part of it, apply only that part.

## Step 5: write and verify

Write the merged file. Then verify, per agent:

| Agent | Verification |
| --- | --- |
| Bob | Confirm `~/.bob/settings/settings.json` parses as valid JSON. |
| Claude Code | Tell the user to run `/permissions`. Restart is not required. |
| Codex | `codex execpolicy check --pretty --rules ~/.codex/rules/default.rules -- git push --force` should report `forbidden`. |
| OpenCode | Confirm the file parses as JSON. |
| Oh My Pi | Confirm the file parses as YAML. |
| Droid | Confirm the file parses as JSON. |
| Cursor CLI | Confirm the file parses as JSON. |

Finally, tell the user two things about what they now have:

- Rules are enforced by the harness, not by the model. An `AGENTS.md` or
  `CLAUDE.md` shapes what an agent tries to do. It does not decide what runs.
- This is one layer. It pairs with a sandbox, it does not replace one.

## If something goes wrong

Do not retry with a broader permission mode, and do not suggest the user
disable permissions to get the install through. If you are blocked from writing
the config file, that is the policy working. Print the merged file and let the
user paste it themselves.
