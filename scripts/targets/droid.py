"""Droid (Factory): ~/.factory/settings.json

commandAllowlist runs without confirmation, commandBlocklist can never run, and
anything unlisted follows the session autonomy level. There is no third tier
that maps onto "ask", so ask rules are deliberately left out and inherit the
default prompt.

Entries are plain command strings. Patterns with an embedded wildcard are
dropped rather than guessed at, which leaves them prompting.
"""

from __future__ import annotations

import json

from ruleset import Ecosystem

PATH = "droid/settings.json"
CONFIG_PATH = "~/.factory/settings.json"


def render(ecosystems: list[Ecosystem]) -> str:
    rules = [r for eco in ecosystems for r in eco.rules if r.is_bash]

    def entries(decision: str) -> list[str]:
        seen: list[str] = []
        for rule in rules:
            if rule.decision == decision and "*" not in rule.pattern:
                if rule.pattern not in seen:
                    seen.append(rule.pattern)
        return seen

    config = {
        "sessionDefaultSettings": {"autonomyLevel": "medium"},
        "commandAllowlist": entries("allow"),
        "commandBlocklist": entries("deny"),
    }
    return json.dumps(config, indent=2) + "\n"
