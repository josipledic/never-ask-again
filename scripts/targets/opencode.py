"""OpenCode: ~/.config/opencode/opencode.json (or ./opencode.json per project)

permission.bash maps glob patterns to allow/ask/deny. The last matching rule
wins, which is the opposite of Claude Code, so ordering here runs from the
broadest catch-all down to the strictest rule: "*" first, then allow, then ask,
then deny.
"""

from __future__ import annotations

import json

from ruleset import Ecosystem, Rule

PATH = "opencode/opencode.json"
CONFIG_PATH = "~/.config/opencode/opencode.json"

# OpenCode has no "ask" for path-shaped tools, so Read/Edit denies land in the
# read/edit maps and everything else falls back to the catch-all.
TOOL_KEY = {"Read": "read", "Edit": "edit", "WebFetch": "webfetch"}


def _pattern(rule: Rule) -> str:
    return rule.pattern if rule.exact else f"{rule.pattern} *"


def render(ecosystems: list[Ecosystem]) -> str:
    rules = [r for eco in ecosystems for r in eco.rules]

    bash: dict[str, str] = {"*": "ask"}
    for decision in ("allow", "ask", "deny"):
        for rule in rules:
            if rule.is_bash and rule.decision == decision:
                bash[_pattern(rule)] = decision

    permission: dict[str, object] = {"bash": bash}

    for tool, key in TOOL_KEY.items():
        entries = {
            r.pattern: r.decision
            for r in rules
            if r.tool == tool and r.pattern and r.decision != "allow"
        }
        if entries:
            permission[key] = {"*": "allow", **entries}

    config = {
        "$schema": "https://opencode.ai/config.json",
        "permission": permission,
    }
    return json.dumps(config, indent=2) + "\n"
