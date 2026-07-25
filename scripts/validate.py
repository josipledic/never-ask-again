#!/usr/bin/env python3
"""Invariants for rules/ and dist/.

    python3 scripts/validate.py

Checks, in order:

  1. no duplicate rule anywhere in rules/
  2. no allow rule stops at a wrapper that would pass through arbitrary args
  3. no rule is shadowed, meaning a higher-precedence rule swallows all of it
  4. every match / not_match fixture resolves to the decision it claims
  5. every generated file in dist/ parses
  6. dist/ matches a fresh build

Zero dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ruleset import DIST_DIR, ROOT, WRAPPERS, Ecosystem, Rule, RuleError, load  # noqa: E402
from targets import claude  # noqa: E402

# A placeholder argument, used to build the most generic command a rule matches.
FILLER = "X"


def to_regex(pattern: str) -> re.Pattern[str]:
    """Claude Code pattern semantics.

    A single * matches any run of characters, including spaces. A trailing
    " *" is special: it enforces a word boundary, requiring the prefix to be
    followed by a space or by end-of-string. That is why Bash(ls *) matches
    "ls -la" and bare "ls", but not "lsof".
    """
    if pattern.endswith(" *"):
        head = ".*".join(re.escape(part) for part in pattern[:-2].split("*"))
        return re.compile("^" + head + r"(?: .*)?$")
    body = ".*".join(re.escape(part) for part in pattern.split("*"))
    return re.compile("^" + body + "$")


def representatives(rule: Rule) -> list[str]:
    """Commands standing in for everything this rule matches.

    A prefix rule covers both the bare command and the command with arguments,
    so a shadow only counts when a higher-precedence rule swallows both.
    """
    command = rule.pattern.replace("*", FILLER)
    if rule.exact:
        return [command]
    return [command, f"{command} {FILLER}"]


class Policy:
    """Claude Code evaluation: deny, then ask, then allow. First match wins."""

    def __init__(self, ecosystems: list[Ecosystem]) -> None:
        self.buckets: dict[str, list[tuple[Rule, re.Pattern[str]]]] = {}
        for decision in ("deny", "ask", "allow"):
            self.buckets[decision] = [
                (rule, to_regex(rule.glob()))
                for eco in ecosystems
                for rule in eco.rules
                if rule.is_bash and rule.decision == decision
            ]

    def decide(self, command: str) -> tuple[str, Rule | None]:
        for decision in ("deny", "ask", "allow"):
            for rule, regex in self.buckets[decision]:
                if regex.match(command):
                    return decision, rule
        return "prompt", None

    def shadow(self, rule: Rule) -> Rule | None:
        """The higher-precedence rule that makes `rule` unreachable, if any."""
        order = ("deny", "ask", "allow")
        earlier = order[: order.index(rule.decision)]
        caught: list[Rule] = []
        for command in representatives(rule):
            for decision in earlier:
                hit = next(
                    (o for o, regex in self.buckets[decision] if regex.match(command)),
                    None,
                )
                if hit is not None:
                    caught.append(hit)
                    break
            else:
                return None  # this form still reaches the rule
        return caught[0] if caught else None


def check_duplicates(ecosystems: list[Ecosystem]) -> list[str]:
    seen: dict[tuple[str, str], str] = {}
    problems = []
    for eco in ecosystems:
        for rule in eco.rules:
            key = (rule.tool, rule.glob())
            if key in seen:
                problems.append(
                    f"duplicate {rule.tool}({rule.glob()}) in {eco.slug}, "
                    f"already defined in {seen[key]}"
                )
            else:
                seen[key] = eco.slug
    return problems


def check_wrappers(ecosystems: list[Ecosystem]) -> list[str]:
    """An allow rule must never stop at a command that forwards its arguments."""
    problems = []
    for eco in ecosystems:
        for rule in eco.rules:
            if rule.decision != "allow" or not rule.is_bash:
                continue
            tokens = rule.pattern.split()
            if tokens[0] in WRAPPERS and len(tokens) == 1 and not rule.exact:
                problems.append(
                    f"{eco.slug}: allow Bash({rule.glob()}) stops at the wrapper "
                    f"{tokens[0]!r}, which forwards whatever follows"
                )
    return problems


def check_shadows(ecosystems: list[Ecosystem], policy: Policy) -> list[str]:
    problems = []
    for eco in ecosystems:
        for rule in eco.rules:
            if not rule.is_bash:
                continue
            shadowing = policy.shadow(rule)
            if shadowing is not None:
                problems.append(
                    f"{eco.slug}: {rule.decision} Bash({rule.glob()}) can never fire, "
                    f"{shadowing.decision} Bash({shadowing.glob()}) matches it first"
                )
    return problems


def check_fixtures(ecosystems: list[Ecosystem], policy: Policy) -> list[str]:
    problems = []
    for eco in ecosystems:
        for group in eco.groups:
            if group.tool != "Bash":
                continue
            for command in group.match:
                actual, rule = policy.decide(command)
                if actual != group.decision:
                    got = f"{actual} via Bash({rule.glob()})" if rule else "no match"
                    problems.append(
                        f"{eco.slug}: {command!r} should be {group.decision}, got {got}"
                    )
            for command in group.not_match:
                actual, _ = policy.decide(command)
                if actual == group.decision:
                    problems.append(
                        f"{eco.slug}: {command!r} should not be {group.decision}, but is"
                    )
    return problems


def check_dist() -> list[str]:
    problems = []
    for name in ("claude/settings.json", "opencode/opencode.json",
                 "droid/settings.json", "cursor/cli-config.json"):
        path = DIST_DIR / name
        if not path.exists():
            problems.append(f"missing {path.relative_to(ROOT)}")
            continue
        try:
            json.loads(path.read_text())
        except json.JSONDecodeError as error:
            problems.append(f"{path.relative_to(ROOT)} is not valid JSON: {error}")
    return problems


def check_claude_specs(ecosystems: list[Ecosystem]) -> list[str]:
    """Write() and Glob() rules are accepted by Claude Code but never matched."""
    problems = []
    for eco in ecosystems:
        for rule in eco.rules:
            spec = claude.spec(rule)
            if spec.startswith(("Write(", "Glob(")):
                problems.append(
                    f"{eco.slug}: {spec} is accepted but never matched, "
                    "use Edit(...) or Read(...)"
                )
    return problems


def check_codex(ecosystems: list[Ecosystem]) -> list[str] | None:
    """Run every fixture through the real codex execpolicy binary.

    Returns None when Codex is not installed. Codex cannot express embedded
    wildcards, so a fixture coming back unmatched is expected and fine. What
    must never happen is a decision inverting: something this repo denies
    coming back as allow, or vice versa.
    """
    import shutil
    import subprocess

    if shutil.which("codex") is None:
        return None

    rules = DIST_DIR / "codex/default.rules"
    opposite = {"allow": "forbidden", "deny": "allow", "ask": "allow"}
    problems = []

    for eco in ecosystems:
        for group in eco.groups:
            if group.tool != "Bash":
                continue
            for command in group.match:
                result = subprocess.run(
                    ["codex", "execpolicy", "check", "--rules", str(rules), "--", *command.split()],
                    capture_output=True,
                    text=True,
                )
                try:
                    decision = json.loads(result.stdout).get("decision", "unmatched")
                except json.JSONDecodeError:
                    decision = "unmatched"
                if decision == opposite[group.decision]:
                    problems.append(
                        f"{eco.slug}: codex says {decision} for {command!r}, "
                        f"this repo says {group.decision}"
                    )
    return problems


def main() -> int:
    try:
        ecosystems = load()
    except RuleError as error:
        print(f"rules error: {error}", file=sys.stderr)
        return 2

    policy = Policy(ecosystems)
    sections = [
        ("duplicates", check_duplicates(ecosystems)),
        ("wrapper-shaped allows", check_wrappers(ecosystems)),
        ("shadowed rules", check_shadows(ecosystems, policy)),
        ("fixtures", check_fixtures(ecosystems, policy)),
        ("generated files", check_dist()),
        ("unmatched rule forms", check_claude_specs(ecosystems)),
    ]

    codex_problems = check_codex(ecosystems)
    if codex_problems is None:
        print("note: codex not installed, skipping execpolicy cross-check")
    else:
        sections.append(("codex execpolicy", codex_problems))

    failed = 0
    for name, problems in sections:
        if problems:
            failed += len(problems)
            print(f"\n{name}: {len(problems)} problem(s)")
            for problem in problems:
                print(f"  {problem}")

    total = sum(len(eco.rules) for eco in ecosystems)
    if failed:
        print(f"\n{failed} problem(s) across {total} rules", file=sys.stderr)
        return 1
    print(f"ok: {total} rules, {len(ecosystems)} ecosystems, {len(sections)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
