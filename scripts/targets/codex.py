"""Codex: ~/.codex/rules/default.rules

Starlark. prefix_rule(pattern, decision, justification, match, not_match) where
pattern is an argv list and a nested list is a union of alternatives at that
position. Most restrictive decision wins.

Codex matches literal argv prefixes with no wildcard support, so any rule with
an embedded "*" cannot be expressed. Those are emitted as comments rather than
silently dropped, and fall through to the approval policy in config.toml.
"""

from __future__ import annotations

from ruleset import Ecosystem, Group, Rule, banner

PATH = "codex/default.rules"
CONFIG_PATH = "~/.codex/rules/default.rules"

DECISION = {"allow": "allow", "ask": "prompt", "deny": "forbidden"}

HEADER = """
# decision = "allow"     -> run without prompting
# decision = "prompt"    -> ask every time
# decision = "forbidden" -> block without prompting
#
# Most restrictive match wins: forbidden > prompt > allow.
#
# Test before trusting:
#   codex execpolicy check --pretty --rules ~/.codex/rules/default.rules -- git add .
"""


def _literal(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _list(values: list[str]) -> str:
    return "[" + ", ".join(_literal(v) for v in values) + "]"


def _expressible(rule: Rule) -> bool:
    return rule.is_bash and "*" not in rule.pattern


def _pattern(tokens: list[str]) -> str:
    return "[" + ", ".join(_literal(t) for t in tokens) + "]"


def _emit(pattern: str, group: Group) -> list[str]:
    return [
        "prefix_rule(",
        f"    pattern = {pattern},",
        f'    decision = "{DECISION[group.decision]}",',
        f"    justification = {_literal(group.why)},",
        ")",
        "",
    ]


def _group_lines(group: Group) -> list[str]:
    usable = [r for r in group.rules if _expressible(r)]
    skipped = [r for r in group.rules if r.is_bash and not _expressible(r)]

    lines: list[str] = []
    if not usable and skipped:
        lines.append(f"# {group.why}")

    # Bucket by first token so sibling subcommands collapse into one union.
    buckets: dict[str, list[list[str]]] = {}
    for rule in usable:
        tokens = rule.pattern.split()
        buckets.setdefault(tokens[0], []).append(tokens[1:])

    # Bare commands sharing a decision become a union in the first position,
    # the same shape the docs use for [["gcloud", "az"], "auth"].
    bare = [base for base, remainders in buckets.items() if remainders == [[]]]
    if len(bare) > 1:
        lines += _emit(f"[{_list(bare)}]", group)

    for base, remainders in buckets.items():
        if base in bare and len(bare) > 1:
            continue

        # A union only lines up when every alternative is a single token at the
        # same position. Longer patterns get their own rule.
        singles = [r[0] for r in remainders if len(r) == 1]
        others = [r for r in remainders if len(r) != 1]

        if len(singles) > 1:
            lines += _emit(f"[{_literal(base)}, {_list(singles)}]", group)
        elif singles:
            lines += _emit(_pattern([base, singles[0]]), group)

        for remainder in others:
            lines += _emit(_pattern([base] + remainder), group)

    for rule in skipped:
        lines.append(f"# not expressible in Codex (embedded wildcard): {rule.glob()}")
    if skipped:
        lines.append("")
    return lines


def render(ecosystems: list[Ecosystem]) -> str:
    lines = banner()
    lines.append("#")
    lines += [line for line in HEADER.strip("\n").split("\n")]
    lines.append("")

    for eco in ecosystems:
        body: list[str] = []
        for group in eco.groups:
            if group.tool != "Bash":
                continue
            body += _group_lines(group)
        if not body:
            continue
        lines.append("# " + "-" * 73)
        lines.append(f"# {eco.name.lower()}: {eco.description}")
        lines.append("# " + "-" * 73)
        lines.append("")
        lines += body

    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"
