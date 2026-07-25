"""Oh My Pi: ~/.omp/agent/config.yml

bash.patterns is an ordered list of {match, approval} where the FIRST matching
rule wins. That is the opposite of OpenCode, so this file runs strictest first:
deny, then prompt, then allow, with a trailing catch-all that prompts.

Written as YAML by hand because this repo has no dependencies.
"""

from __future__ import annotations

from ruleset import Ecosystem, Rule, banner

PATH = "omp/config.yml"
CONFIG_PATH = "~/.omp/agent/config.yml"

APPROVAL = {"allow": "allow", "ask": "prompt", "deny": "deny"}


def _yaml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _pattern(rule: Rule) -> str:
    return rule.pattern if rule.exact else f"{rule.pattern} *"


def render(ecosystems: list[Ecosystem]) -> str:
    lines = banner()
    lines += [
        "#",
        "# bash.patterns is first-match-wins, so this file is ordered",
        "# deny -> prompt -> allow, ending in a catch-all prompt.",
        "",
        "tools:",
        "  approvalMode: write",
        "  approval:",
        "    bash: prompt",
        "",
        "bash:",
        "  patterns:",
    ]

    for decision in ("deny", "ask", "allow"):
        for eco in ecosystems:
            groups = [
                g for g in eco.groups if g.tool == "Bash" and g.decision == decision
            ]
            if not groups:
                continue
            lines.append(f"    # {eco.name}: {decision}")
            for group in groups:
                lines.append(f"    # {group.why}")
                for rule in group.rules:
                    lines.append(f"    - match: {_yaml_str(_pattern(rule))}")
                    lines.append(f"      approval: {APPROVAL[decision]}")

    lines += [
        "    # Anything not named above.",
        '    - match: "*"',
        "      approval: prompt",
    ]
    return "\n".join(lines) + "\n"
