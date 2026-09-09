"""Bob (IBM Bob IDE): ~/.bob/settings/settings.json

approval.allowedExecutors is a list of per-tool allowlists. For the
execute_command tool, approvedCommands is a prefix allowlist: "go test"
matches "go test ./..." and any other invocation starting with those tokens.
Commands not in the list prompt. deniedCommands is left empty because the
allowlist already restricts what runs unattended; a separate deny list is not
needed for this use case.

ask and deny rules are omitted -- they are the default behaviour (prompt).
Wildcard-only patterns are skipped because a bare "*" would match everything.
"""

from __future__ import annotations

import json

from ruleset import Ecosystem

PATH = "bob/settings.json"
CONFIG_PATH = "~/.bob/settings/settings.json"


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
        "approval": {
            "allowedExecutors": [
                {
                    "toolId": "execute_command",
                    "approvedCommands": allowed,
                    "deniedCommands": [],
                }
            ]
        }
    }
    return json.dumps(config, indent=2) + "\n"
