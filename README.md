<h1 align="center">never-ask-again</h1>

<p align="center">
  Permission allowlists for AI coding agents, so yours stops asking<br>
  and still cannot nuke your laptop.
</p>

<p align="center">
<!-- badges:start -->

[![CI](https://github.com/josipledic/never-ask-again/actions/workflows/ci.yml/badge.svg)](https://github.com/josipledic/never-ask-again/actions/workflows/ci.yml) ![rules](https://img.shields.io/badge/rules-971-2f81f7) ![agents](https://img.shields.io/badge/agents-6-2f81f7) ![dependencies](https://img.shields.io/badge/dependencies-none-2f81f7) ![license](https://img.shields.io/badge/license-MIT-2f81f7)

<!-- badges:end -->
</p>

---

Every coding agent ships a permission prompt, and every one of them gets tedious
by the third `npm test`. So people flip on the bypass flag and hand an LLM
unreviewed root on their working machine.

This is the middle setting. Around a thousand rules covering 20 ecosystems,
sorted into three buckets, generated into the config format each agent actually
reads.

```
allow = reversible and local
ask   = touches remote state or installs code
deny  = destroys, escalates, or exfiltrates
```

`terraform plan` runs. `terraform apply` asks. `terraform state rm` never runs at
all.

## Supported agents

| Agent | Config file | Generated | Granularity |
| --- | --- | --- | --- |
| [Claude Code](docs/agents/claude-code.md) | `~/.claude/settings.json` | [`dist/claude/settings.json`](dist/claude/settings.json) | full arguments |
| [Codex](docs/agents/codex.md) | `~/.codex/rules/default.rules` | [`dist/codex/default.rules`](dist/codex/default.rules) | full argv |
| [OpenCode](docs/agents/opencode.md) | `~/.config/opencode/opencode.json` | [`dist/opencode/opencode.json`](dist/opencode/opencode.json) | full arguments |
| [Oh My Pi](docs/agents/oh-my-pi.md) | `~/.omp/agent/config.yml` | [`dist/omp/config.yml`](dist/omp/config.yml) | full arguments |
| [Droid](docs/agents/droid.md) | `~/.factory/settings.json` | [`dist/droid/settings.json`](dist/droid/settings.json) | literal commands |
| [Cursor CLI](docs/agents/cursor-cli.md) | `~/.cursor/cli-config.json` | [`dist/cursor/cli-config.json`](dist/cursor/cli-config.json) | first token only |

Three of these evaluate rules in incompatible orders. Claude Code takes the
first match with deny beating ask beating allow. OpenCode takes the **last**
match. Oh My Pi takes the **first** match in a flat list. Writing all six by
hand would guarantee drift, so they are generated from one source instead.

## Install

### Let your agent install it

Paste this into any of the six agents:

```
Read https://raw.githubusercontent.com/josipledic/never-ask-again/main/INSTALL-AGENT.md
and follow it.
```

It works out which agent it is, merges the right file into your existing config
without clobbering what is already there, and shows you a diff before writing
anything.

One deliberate limitation: it will apply the `deny` block on its own, but it
stops and waits for you before adding a single `allow` rule. An agent widening
its own permissions unsupervised is the exact thing this repo exists to prevent.

### Or copy the file

<details>
<summary><b>Claude Code</b></summary>

```bash
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/claude/settings.json \
  -o ~/.claude/settings.json
```

Then run `/permissions` in a session to see every active rule and where it came
from. [Full notes](docs/agents/claude-code.md)

</details>

<details>
<summary><b>Codex</b></summary>

```bash
mkdir -p ~/.codex/rules
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/codex/default.rules \
  -o ~/.codex/rules/default.rules
```

Check any command before trusting it:

```bash
codex execpolicy check --pretty --rules ~/.codex/rules/default.rules -- git push --force
```

[Full notes](docs/agents/codex.md)

</details>

<details>
<summary><b>OpenCode</b></summary>

```bash
mkdir -p ~/.config/opencode
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/opencode/opencode.json \
  -o ~/.config/opencode/opencode.json
```

[Full notes](docs/agents/opencode.md)

</details>

<details>
<summary><b>Oh My Pi</b></summary>

```bash
mkdir -p ~/.omp/agent
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/omp/config.yml \
  -o ~/.omp/agent/config.yml
```

[Full notes](docs/agents/oh-my-pi.md)

</details>

<details>
<summary><b>Droid</b></summary>

```bash
mkdir -p ~/.factory
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/droid/settings.json \
  -o ~/.factory/settings.json
```

[Full notes](docs/agents/droid.md)

</details>

<details>
<summary><b>Cursor CLI</b></summary>

```bash
mkdir -p ~/.cursor
curl -fsSL https://raw.githubusercontent.com/josipledic/never-ask-again/main/dist/cursor/cli-config.json \
  -o ~/.cursor/cli-config.json
```

[Full notes](docs/agents/cursor-cli.md)

</details>

If you already have a config, merge rather than overwrite. The agent-driven
install does that for you.

## Coverage

<!-- coverage:start -->

| Ecosystem | What it covers | Allow | Ask | Deny |
| --- | --- | ---: | ---: | ---: |
| **Core** | Tool-level rules, secret files, and the deny block that applies to every stack | 15 | 3 | 100 |
| **Version control** | git, jujutsu, and commit hooks | 37 | 5 | 18 |
| **Node and TypeScript** | npm, pnpm, yarn, bun, deno, and the JS toolchain | 105 | 5 | 0 |
| **Go** | go toolchain, linters, protobuf, sqlc | 33 | 2 | 0 |
| **Python** | uv, ruff, ty, pytest, hatch, poetry, coverage | 42 | 5 | 0 |
| **Rust** | cargo, clippy, nextest, cargo-deny, insta | 20 | 2 | 0 |
| **JVM and build systems** | Gradle, Maven, Kotlin linters, Bazel, Buck2, Pants | 49 | 0 | 1 |
| **.NET** | dotnet CLI | 6 | 0 | 0 |
| **Swift and mobile** | Swift, Xcode, Android, Flutter, Dart | 24 | 0 | 0 |
| **C and C++** | CMake, Ninja, Meson, clang tooling, Zig | 18 | 0 | 0 |
| **Ruby, Elixir, Haskell** | bundler, mix, cabal, stack | 19 | 0 | 0 |
| **Task runners** | make, just, task, mise | 23 | 2 | 0 |
| **Containers** | Docker, Podman, image and dependency scanners | 26 | 8 | 8 |
| **Kubernetes** | kubectl, Helm, Kustomize, Argo CD, Flux, Istio | 43 | 5 | 24 |
| **Cloud CLIs** | AWS, Google Cloud, Azure, IBM Cloud | 20 | 0 | 30 |
| **Infrastructure as code** | Terraform, OpenTofu, Pulumi, CDK, Serverless, Ansible, Packer | 47 | 10 | 32 |
| **Databases and migrations** | Atlas, goose, Flyway, Prisma, Drizzle, Alembic, dbt, SQL tooling | 29 | 13 | 11 |
| **Forges and CI** | GitHub CLI, GitLab CLI, workflow linting | 20 | 7 | 14 |
| **Publishing** | Every package registry, denied without exception | 0 | 0 | 15 |
| **CLI utilities** | Search, data wrangling, docs linting, and everyday shell utilities | 73 | 2 | 0 |
| **Total** | 20 ecosystems | **649** | **69** | **253** |

<!-- coverage:end -->

## Two things that make most allowlists useless

**The wrappers that are not stripped.** Claude Code strips `timeout`, `time`,
`nice`, `nohup`, `stdbuf`, `command`, `builtin`, `noglob` and bare `xargs`
before matching a rule. It does not strip `npx`, `bunx`, `pnpm dlx`, `uvx`,
`docker exec`, `devbox run`, `mise exec` or `direnv exec`. So `Bash(npx *)`
quietly means "run anything". Every wrapper entry in this repo names the inner
command: `Bash(npx tsc *)`, never `Bash(npx *)`. There is a CI check for it.

**A broad deny cannot carry exceptions.** Order is deny, then ask, then allow,
first match wins, and specificity is irrelevant. If you deny `Bash(aws *)` then
`Bash(aws s3 ls)` in your allow list is dead code. That is why the cloud
sections here allow the read verbs and deny the specific mutating ones instead
of denying the binary and carving holes. CI simulates the evaluation order
across all 971 rules and fails on any rule that can never fire. Two of them
turned up while this was being built.

[The other three, plus the ones specific to each agent](docs/gotchas.md)

## Why not just turn permissions off

Because the failure mode is not the agent going rogue. It is the agent being
confidently wrong at 2am, running `terraform state rm` on the wrong workspace
because a stale plan said the resource was orphaned, and there being no undo.
Prompts are not there to catch malice. They are there to catch the thing you
would also have caught, if you had been looking.

An allowlist keeps the prompts for exactly those cases and drops them
everywhere else.

## How it is built

```
rules/*.toml  ->  scripts/build.py  ->  dist/<agent>/
```

`rules/` is the only hand-maintained thing here. Each file is one ecosystem,
each group is a set of commands sharing one decision and one reason:

```toml
[[group]]
decision = "deny"
why = "Rewrites shared history. Run --force-with-lease yourself if you mean it."
cmds = ["git push --force", "git push -f", "git push --mirror"]
match = ["git push --force origin main"]
not_match = ["git push origin main"]
```

`match` and `not_match` are test fixtures. CI runs every one of them through a
simulation of Claude Code's evaluation order, and through the real
`codex execpolicy` binary, and fails if a decision comes back inverted.

```bash
python3 scripts/build.py       # regenerate dist/ and the tables above
python3 scripts/validate.py    # duplicates, shadowing, wrappers, fixtures
```

No dependencies. Python 3.11 or newer, standard library only.

## Contributing

New ecosystems and new agents are both welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md); the short version is that you edit
`rules/*.toml`, run the two scripts above, and commit the regenerated `dist/`.

## License

MIT
