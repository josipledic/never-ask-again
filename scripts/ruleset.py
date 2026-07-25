"""Loader for the rules/ source of truth.

Every generated config in dist/ comes from these TOML files. Nothing else in
this repo is hand-maintained.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
DIST_DIR = ROOT / "dist"

DECISIONS = ("allow", "ask", "deny")

# Wrappers that pass their remaining arguments to another program. An allow
# rule that stops at one of these grants whatever the wrapper is handed.
WRAPPERS = frozenset(
    {
        "npx", "bunx", "uvx", "pnpm", "yarn", "npm", "deno",
        "docker", "podman", "mise", "devbox", "direnv", "nix",
        "xargs", "sh", "bash", "zsh", "env", "sudo", "doas",
        "poetry", "uv", "bundle", "hatch", "tox", "nox", "rye", "pdm",
    }
)


@dataclass(frozen=True)
class Rule:
    """One command pattern with one decision."""

    pattern: str
    decision: str
    why: str
    ecosystem: str
    tool: str = "Bash"
    exact: bool = False

    @property
    def base(self) -> str:
        """First token of the command, e.g. "kubectl" for "kubectl get"."""
        return self.pattern.split(" ", 1)[0]

    @property
    def is_bash(self) -> bool:
        return self.tool == "Bash"

    def glob(self) -> str:
        """The pattern as a shell-style glob: what a matching command looks like."""
        return self.pattern if self.exact else f"{self.pattern} *"


@dataclass
class Group:
    """A set of commands that share one decision and one rationale.

    Groups exist because rationales are worth writing once for a coherent set
    of commands, not 973 times. They also map directly onto Codex prefix_rule
    unions and onto the blank-line grouping in the Claude Code settings file.
    """

    decision: str
    why: str
    ecosystem: str
    tool: str = "Bash"
    rules: list[Rule] = field(default_factory=list)
    match: list[str] = field(default_factory=list)
    not_match: list[str] = field(default_factory=list)


@dataclass
class Ecosystem:
    name: str
    slug: str
    description: str
    order: int
    path: Path
    groups: list[Group] = field(default_factory=list)

    @property
    def rules(self) -> list[Rule]:
        return [rule for group in self.groups for rule in group.rules]

    def counts(self) -> dict[str, int]:
        counts = dict.fromkeys(DECISIONS, 0)
        for rule in self.rules:
            counts[rule.decision] += 1
        return counts


class RuleError(Exception):
    """A rules/ file is malformed. Raised with the offending file named."""


def _load_file(path: Path) -> Ecosystem:
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    def require(key: str) -> object:
        if key not in data:
            raise RuleError(f"{path.name}: missing top-level '{key}'")
        return data[key]

    eco = Ecosystem(
        name=str(require("name")),
        slug=str(require("slug")),
        description=str(require("description")),
        order=int(require("order")),
        path=path,
    )

    for index, raw in enumerate(data.get("group", [])):
        where = f"{path.name} group #{index + 1}"

        decision = raw.get("decision")
        if decision not in DECISIONS:
            raise RuleError(f"{where}: decision must be one of {DECISIONS}, got {decision!r}")

        why = str(raw.get("why", "")).strip()
        if not why:
            raise RuleError(f"{where}: every group needs a non-empty 'why'")

        tool = str(raw.get("tool", "Bash"))
        group = Group(
            decision=decision,
            why=why,
            ecosystem=eco.slug,
            tool=tool,
            match=[str(m) for m in raw.get("match", [])],
            not_match=[str(m) for m in raw.get("not_match", [])],
        )

        if tool == "Bash":
            if raw.get("args"):
                raise RuleError(f"{where}: 'args' is for tool rules; Bash groups use 'cmds'/'exact'")
            for cmd in raw.get("cmds", []):
                group.rules.append(
                    Rule(str(cmd), decision, why, eco.slug, exact=False)
                )
            for cmd in raw.get("exact", []):
                group.rules.append(
                    Rule(str(cmd), decision, why, eco.slug, exact=True)
                )
        else:
            if raw.get("cmds") or raw.get("exact"):
                raise RuleError(f"{where}: tool groups use 'args', not 'cmds'/'exact'")
            args = raw.get("args")
            if args is None:
                # A bare tool rule with no specifier, e.g. allow "Read" outright.
                group.rules.append(Rule("", decision, why, eco.slug, tool=tool, exact=True))
            else:
                for arg in args:
                    group.rules.append(
                        Rule(str(arg), decision, why, eco.slug, tool=tool, exact=True)
                    )

        if not group.rules:
            raise RuleError(f"{where}: no rules")
        eco.groups.append(group)

    if not eco.groups:
        raise RuleError(f"{path.name}: no groups")
    return eco


def load(rules_dir: Path = RULES_DIR) -> list[Ecosystem]:
    """Load every rules/*.toml, ordered by 'order' then slug."""
    paths = sorted(rules_dir.glob("*.toml"))
    if not paths:
        raise RuleError(f"no rule files found in {rules_dir}")
    ecosystems = [_load_file(path) for path in paths]
    ecosystems.sort(key=lambda eco: (eco.order, eco.slug))
    return ecosystems


def all_rules(ecosystems: list[Ecosystem]) -> list[Rule]:
    return [rule for eco in ecosystems for rule in eco.rules]


def all_groups(ecosystems: list[Ecosystem]) -> list[Group]:
    return [group for eco in ecosystems for group in eco.groups]


def bash_rules(ecosystems: list[Ecosystem], decision: str | None = None) -> list[Rule]:
    rules = [rule for rule in all_rules(ecosystems) if rule.is_bash]
    if decision is not None:
        rules = [rule for rule in rules if rule.decision == decision]
    return rules


def banner(comment: str = "#") -> list[str]:
    """The do-not-edit header every generated file carries."""
    return [
        f"{comment} Generated by scripts/build.py from rules/*.toml. Do not edit by hand.",
        f"{comment} https://github.com/josipledic/never-ask-again",
    ]
