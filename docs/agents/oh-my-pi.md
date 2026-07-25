# Oh My Pi

Generated file: [`dist/omp/config.yml`](../../dist/omp/config.yml)

Oh My Pi is the `omp` CLI, [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi).

## Install

```bash
mkdir -p ~/.omp/agent
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/omp/config.yml \
  -o ~/.omp/agent/config.yml
```

The global config must be YAML. A per-project config at `.omp/config.yml`
accepts YAML or JSON.

## Rule format

```yaml
tools:
  approvalMode: write
  approval:
    bash: prompt

bash:
  patterns:
    - match: "git *"
      approval: allow
    - match: "rm -rf *"
      approval: deny
    - match: "*"
      approval: prompt
```

`approval` is `allow`, `prompt` or `deny`. Patterns are literal text plus `*`
as a wildcard.

`tools.approvalMode` sets the global tier: `always-ask` auto-approves reads
only, `write` auto-approves reads and writes and prompts for exec, and `yolo`
auto-approves everything. The generated file sets `write`, which is the
equivalent of Claude Code's `acceptEdits`.

## Evaluation order: first match wins

The **first** matching pattern wins, which is the opposite of OpenCode. The
generated file is ordered strictest to broadest: every deny first, then every
prompt, then every allow, ending in a `"*"` catch-all that prompts.

If you hand-edit it, put new deny rules near the top. A deny added at the
bottom will never be reached, because the catch-all above it matches first.

## Note on critical commands

Oh My Pi keeps its own guards for destructive patterns like `rm -rf /`, and a
broad `match: "*"` with `approval: allow` does not bypass them. That is a
backstop, not a substitute for the deny list.
