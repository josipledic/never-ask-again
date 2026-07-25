"""Cursor CLI: ~/.cursor/cli-config.json

Shell() matches only the first token of a command, so "kubectl get" and
"kubectl delete" are indistinguishable here. This target therefore degrades
conservatively:

  every rule under a base is allow  -> Shell(base) in allow
  every rule under a base is deny   -> Shell(base) in deny
  anything mixed                    -> omitted, so it prompts

That makes the generated file coarser than the others by construction. A base
like kubectl, which this repo allows for reads and denies for writes, ends up
prompting rather than being wrongly allowed.
"""

from __future__ import annotations

import json

from ruleset import Ecosystem

PATH = "cursor/cli-config.json"
CONFIG_PATH = "~/.cursor/cli-config.json"


def _shell_tokens(ecosystems: list[Ecosystem]) -> tuple[list[str], list[str], list[str]]:
    bases: dict[str, set[str]] = {}
    for eco in ecosystems:
        for rule in eco.rules:
            if rule.is_bash:
                bases.setdefault(rule.base, set()).add(rule.decision)

    allow, deny, mixed = [], [], []
    for base in sorted(bases):
        decisions = bases[base]
        if "*" in base:
            continue
        if decisions == {"allow"}:
            allow.append(f"Shell({base})")
        elif decisions == {"deny"}:
            deny.append(f"Shell({base})")
        else:
            mixed.append(base)
    return allow, deny, mixed


def render(ecosystems: list[Ecosystem]) -> str:
    allow, deny, mixed = _shell_tokens(ecosystems)
    rules = [r for eco in ecosystems for r in eco.rules]

    for rule in rules:
        if rule.tool == "Read" and rule.decision == "deny" and rule.pattern:
            deny.append(f"Read({rule.pattern})")
        elif rule.tool == "Edit" and rule.decision == "deny" and rule.pattern:
            deny.append(f"Write({rule.pattern})")

    config = {
        "permissions": {"allow": allow, "deny": deny},
        "_note": (
            "Cursor matches Shell() on the first token only. "
            f"{len(mixed)} commands that this repo allows for some subcommands and "
            "denies for others are omitted so they prompt: "
            + ", ".join(mixed)
        ),
    }
    return json.dumps(config, indent=2) + "\n"
