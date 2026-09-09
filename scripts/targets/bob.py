"""Bob (IBM Bob IDE): ~/.bob/settings.json (user) or .bob/settings.json (project)

autoApprove.allowedCommands is a flat prefix/substring allowlist. Commands not
in the list prompt regardless of the execute flag. There is no deny list, so
deny and ask rules are simply omitted. execute is set to false so that only
the allowlist entries run unattended.
"""

from __future__ import annotations

import json

from ruleset import Ecosystem

PATH = "bob/settings.json"
CONFIG_PATH = "~/.bob/settings.json"


def render(ecosystems: list[Ecosystem]) -> str:
    rules = [r for eco in ecosystems for r in eco.rules if r.is_bash]

    allowed: list[str] = []
    seen: set[str] = set()
    for rule in rules:
        if rule.decision == "allow" and "*" not in rule.pattern:
            if rule.pattern not in seen:
                seen.add(rule.pattern)
                allowed.append(rule.pattern)

    config = {
        "autoApprove": {
            "read": True,
            "edit": True,
            "execute": False,
            "allowedCommands": allowed,
            "mcp": False,
        }
    }
    return json.dumps(config, indent=2) + "\n"
