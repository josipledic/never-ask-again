# The things that make most allowlists useless

Five of these are general. The rest are specific to one agent and live on that
agent's page.

## 1. Wrappers that are not stripped

Claude Code strips a fixed set of wrappers before matching a rule: `timeout`,
`time`, `nice`, `nohup`, `stdbuf`, `command`, `builtin`, zsh `noglob`, and bare
`xargs`. The list is built in and not configurable.

It does not strip the ones you actually use: `npx`, `bunx`, `pnpm dlx`, `uvx`,
`docker exec`, `devbox run`, `mise exec`, `direnv exec`. Those execute their
arguments as a command, so `Bash(devbox run *)` matches `devbox run rm -rf .`.

Write one rule per inner command:

```json
"Bash(npx tsc *)"        // yes
"Bash(npx *)"            // this means "run anything"
```

`scripts/validate.py` fails the build on any allow rule that stops at a
wrapper.

Separately, `watch`, `setsid`, `ionice` and `flock` always prompt and cannot be
auto-approved by a prefix rule at all. So does `find` with `-exec` or
`-delete`.

## 2. The space before the star

`Bash(ls *)` matches `ls -la` and bare `ls`, but not `lsof`. The trailing
` *` enforces a word boundary, requiring the prefix to be followed by a space
or by the end of the string.

`Bash(ls*)` without the space matches `lsof` too.

`Bash(ls:*)` is an equivalent way to write the first form, but the `:*` suffix
is only recognised at the end of a pattern. In `Bash(git:* push)` the colon is
a literal character and matches nothing.

A `*` anywhere else matches any run of characters including spaces, so
`Bash(git * main)` matches both `git checkout main` and
`git log --oneline main`.

## 3. A broad deny cannot carry exceptions

Order is deny, then ask, then allow. First match wins. Specificity is
irrelevant.

So this does not work:

```json
"deny":  ["Bash(aws *)"],
"allow": ["Bash(aws s3 ls *)"]     // dead. deny matched first.
```

Every cloud section in this repo allows the read verbs and denies the specific
mutating ones, instead of denying the binary and carving holes.

The same trap catches narrower allow rules under a broader `ask`. An allow for
`terraform init -backend=false` is dead if `terraform init` is in `ask`, and an
allow for `kubectl apply --dry-run=client` is dead if `kubectl apply` is
denied. Both of those were in this repo before CI started simulating the
evaluation order, and both are now gone.

## 4. Installs are remote code execution

`npm install` and `pip install` resolve packages from a registry and run their
lifecycle scripts as you. That is arbitrary code from the internet, executed
without review.

They are in `ask`. The lockfile-exact variants are in `allow`, because the
dependency graph is already decided and committed:

```
npm ci
pnpm install --frozen-lockfile
yarn install --immutable
bun install --frozen-lockfile
uv sync
poetry install --sync
bundle install --deployment
```

## 5. This is enforced by the harness, not the model

Your `CLAUDE.md` or `AGENTS.md` shapes what the agent tries to do. It does not
decide what runs. Instructions in a markdown file are input to a language
model, and a language model can be talked out of them.

Permission rules are enforced outside the model, which is what makes them worth
having. Pair them with a sandbox. Two layers.

## Bonus: some rules do nothing

Claude Code runs a built-in set of commands with no prompt in every mode:
`ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`,
`diff`, `stat`, `du`, `cd`, and read-only forms of `git`. The set is not
configurable.

If your allowlist contains `Bash(git status)`, you gained nothing. To require a
prompt for one of these, you need an `ask` or `deny` rule, since allow is
already the default.

## Bonus: allow rules wait for the trust dialog

Allow rules and `additionalDirectories` in a project's committed
`.claude/settings.json` only take effect after you accept the workspace trust
dialog for that folder. Deny and ask rules apply immediately.

So a project config that only ever adds allow rules will look like it is being
ignored until someone clicks through the dialog.
