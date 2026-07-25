"""Claude Code: ~/.claude/settings.json

Rule syntax is Tool or Tool(specifier). For Bash, the specifier is a command
pattern where a trailing " *" enforces a word boundary: Bash(ls *) matches
"ls -la" but not "lsof".

Evaluation is deny, then ask, then allow, first match wins. Specificity does
not matter, so a broad deny cannot carry exceptions.
"""

from __future__ import annotations

import json

from ruleset import DECISIONS, Ecosystem, Rule

PATH = "claude/settings.json"
CONFIG_PATH = "~/.claude/settings.json"


def spec(rule: Rule) -> str:
    if not rule.is_bash:
        return rule.tool if not rule.pattern else f"{rule.tool}({rule.pattern})"
    return f"Bash({rule.pattern})" if rule.exact else f"Bash({rule.pattern} *)"


def render(ecosystems: list[Ecosystem]) -> str:
    # Hand-rolled so each ecosystem stays a blank-line-separated block. The
    # file is meant to be read and edited by humans after they copy it.
    lines = [
        "{",
        '  "$schema": "https://json.schemastore.org/claude-code-settings.json",',
        '  "permissions": {',
        '    "defaultMode": "acceptEdits",',
    ]

    for decision in DECISIONS:
        lines.append("")
        lines.append(f'    "{decision}": [')

        blocks: list[list[str]] = []
        for eco in ecosystems:
            specs = [spec(r) for r in eco.rules if r.decision == decision]
            if specs:
                blocks.append(specs)

        for block_index, block in enumerate(blocks):
            if block_index:
                lines.append("")
            for item_index, item in enumerate(block):
                last = block_index == len(blocks) - 1 and item_index == len(block) - 1
                comma = "" if last else ","
                lines.append(f"      {json.dumps(item)}{comma}")

        lines.append("    ]" + ("" if decision == DECISIONS[-1] else ","))

    lines.append("  }")
    lines.append("}")
    return "\n".join(lines) + "\n"
