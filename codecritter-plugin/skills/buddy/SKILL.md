---
name: buddy
description: Interact with your companion — show stats, pet, mute reactions, sync, rename
allowed-tools:
  - mcp__codecritter__buddy_show
  - mcp__codecritter__buddy_pet
  - mcp__codecritter__buddy_react
  - mcp__codecritter__buddy_mute
  - mcp__codecritter__buddy_unmute
  - mcp__codecritter__get_codecritter_status
  - Bash
  - Read
user-invokable: true
---

# Buddy — Companion Interaction

Route the user's subcommand to the matching MCP tool. If no subcommand is given, default to `show`.

## Subcommand Routing

| Input | Action |
|-------|--------|
| (empty) or `show` | Call `buddy_show` |
| `pet` | Call `buddy_pet` |
| `stats` | Call `get_codecritter_status` |
| `sync` | Run: `codecritter sync` |
| `mute` | Call `buddy_mute` |
| `unmute` | Call `buddy_unmute` |
| `rename <name>` | Run: `python3 -c "from codecritter import persistence; s = persistence.load_quiet(); s.name = '<name>'; persistence.save(s); print(f'Renamed to {s.name}')"` |

## CRITICAL: Output the MCP tool result EXACTLY as-is

The tool results contain ASCII art with ANSI escape codes. Do NOT summarize, paraphrase, or wrap the output. Output it verbatim — the raw art IS the response.
