# never-ask-again

Permission allowlists for Claude Code and Codex, so your agent stops asking and still cannot nuke your laptop.

Roughly 970 rules across 40+ ecosystems: git, Node, Go, Python, Rust, JVM, Swift, .NET, C++, Bazel, Buck2, Docker, Kubernetes, Terraform, Pulumi, CDK, AWS, GCP, Azure, databases, migrations, forges, linters. Grouped so you can delete what you do not use.

```
claude-settings.json   -> ~/.claude/settings.json
default.rules          -> ~/.codex/rules/default.rules
```

## Install

**Claude Code**

```bash
# global, every project
cp claude-settings.json ~/.claude/settings.json

# or per project, committed and shared with the team
mkdir -p .claude && cp claude-settings.json .claude/settings.json

# or per project, personal and gitignored
mkdir -p .claude && cp claude-settings.json .claude/settings.local.json
```

Then run `/permissions` in a session to see every active rule and which file it came from.

Precedence, highest first: managed settings, CLI flags, `.claude/settings.local.json`, `.claude/settings.json`, `~/.claude/settings.json`. A deny at any level beats an allow at every other level.

**Codex**

```bash
mkdir -p ~/.codex/rules && cp default.rules ~/.codex/rules/default.rules
```

In `~/.codex/config.toml`:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
```

Verify a rule actually does what you think:

```bash
codex execpolicy check --pretty --rules ~/.codex/rules/default.rules -- git add .
```

Rules are still marked experimental in the Codex docs, so re-check after upgrades.

## The five things that make most allowlists useless

**1. Wrappers that are not stripped.** Claude Code strips `timeout`, `time`, `nice`, `nohup`, `stdbuf`, `command`, `builtin`, `noglob` and bare `xargs` before matching. It does not strip `npx`, `bunx`, `pnpm dlx`, `uvx`, `docker exec`, `devbox run`, `mise exec` or `direnv exec`. So `Bash(npx *)` means "run anything". Every wrapper entry in this repo names the inner command: `Bash(npx tsc *)`, never `Bash(npx *)`.

**2. The space before the star.** `Bash(ls *)` matches `ls -la` but not `lsof`. `Bash(ls*)` matches both. The space enforces a word boundary. `Bash(ls:*)` is equivalent to `Bash(ls *)`, but the colon form only works at the end of a pattern.

**3. Precedence, and what it forbids.** Order is deny, then ask, then allow. First match wins, specificity does not matter. A broad deny cannot carry exceptions: if you deny `Bash(aws *)` then `Bash(aws s3 ls)` in allow is dead. That is why the cloud sections here allow the read verbs and deny the specific mutating ones, instead of denying the binary and carving holes.

**4. Installs are remote code execution.** `npm install` and `pip install` run lifecycle scripts from the internet. They are in `ask`, not `allow`. The lockfile-exact variants (`npm ci`, `pnpm install --frozen-lockfile`, `uv sync`) are allowed.

**5. This is enforced by the harness, not the model.** Your `CLAUDE.md` or `AGENTS.md` shapes what the agent tries. It does not decide what runs. If you want a real boundary, turn on the sandbox and put the allowlist on top of it. Two layers.

Bonus: `ls`, `cat`, `grep`, `find`, `head`, `tail`, `wc`, `diff`, `stat`, `du`, `cd` and read-only `git` already run without a prompt in Claude Code. If your allowlist has `Bash(git status)` in it, you gained nothing.

## Design rules

```
allow = reversible and local
ask   = touches remote state or installs code
deny  = destroys, escalates, or exfiltrates
```

Applied consistently, that produces some opinionated calls:

- `terraform plan` is allowed, `terraform apply` is denied, `terraform state rm` is denied harder. Corrupting state is worse than a bad apply.
- `kubectl get` is allowed, every mutating verb is denied, including `kubectl exec`. A shell in a pod is a shell.
- `git restore` and `git checkout -- <file>` are denied. They silently destroy uncommitted work and there is no reflog for it.
- Publishing anything (npm, crates, PyPI, Maven, container registries) is denied everywhere. There is no undo for a published artifact.
- `claude` and `codex` themselves are denied. A nested agent inherits a different permission set.

## Recommended workflow

Do not paste all 970 rules and walk away. Start with the sections for your stack, keep the whole `deny` block, then let the rest build itself: every time you hit a prompt and think "obviously yes", choose "Yes, don't ask again". Claude Code writes it to `.claude/settings.local.json` at your repo root. Every few weeks, promote the good ones to your global file.

One catch: allow rules in a committed `.claude/settings.json` only take effect after you accept the workspace trust dialog for that folder. Deny and ask rules apply immediately.

## Contributing

PRs welcome for stacks that are missing. Two requirements: name the inner command for anything wrapper-shaped, and put every rule in the section for its ecosystem.
