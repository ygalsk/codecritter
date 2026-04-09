# Codecritter Plugin — Terminal Companion

Codecritter is a terminal companion that trains alongside Claude Code sessions. Your companion's species, rarity, eyes, hat, and base stats are deterministically generated from your account UUID — the same algorithm as the original `/buddy` system.

## How It Works

- **Native bones** (species, rarity, base stats, eyes, hat, shiny) are computed deterministically from your account UUID. They're static and never change.
- **TUI progression** (XP, leveling, trained stats, inventory, dungeon) is stored at `~/.claude/codecritter/save.json` and grows as you use Claude Code.
- **Hooks** automatically reward stats when you use tools (Bash -> debugging, Edit -> patience, Write -> wisdom, etc.) and detect errors/test failures for reactions.
- **Reactions** appear in the statusline speech bubble. Claude writes `<!-- buddy: ... -->` comments contextually, and the Stop hook extracts them.
- At session end, TUI progression is pushed back to the native buddy's personality.

## Key Commands

- `/buddy` or `/buddy show` — Show companion card with ASCII art and stats
- `/buddy pet` — Pet the companion (triggers a reaction)
- `/buddy stats` — Detailed stat breakdown
- `/buddy sync` — Bidirectional sync (pull native bones, push TUI progress)
- `/buddy mute` / `/buddy unmute` — Toggle reactions and `<!-- buddy: -->` comments

## Species

18 species: duck, goose, blob, cat, dragon, octopus, owl, penguin, turtle, snail, ghost, axolotl, capybara, cactus, robot, rabbit, mushroom, chonk. Your species is determined by your account UUID.

## Stats Reference

5 stats: DEBUGGING, PATIENCE, CHAOS, WISDOM, SNARK (0-255, capped by rarity).

Rarity caps:
- Common: stat cap 150, level cap 20
- Uncommon: stat cap 180, level cap 30
- Rare: stat cap 220, level cap 50
- Epic: stat cap 245, level cap 75
- Legendary: stat cap 255, level cap 100

## Statusline

To enable the animated statusline, add to your Claude Code settings:
```json
"statusLine": {
  "type": "command",
  "command": "<path-to-codecritter-plugin>/statusline/codecritter-status.sh",
  "refreshInterval": 1
}
```

## Reading State

Always read `~/.claude/codecritter/save.json` for current stats. Key fields:
- `species`: The companion species (e.g., "Duck", "Ghost")
- `eyes`, `hat`, `shiny`: Cosmetic bones data
- `reaction`, `reaction_ts`: Current speech bubble text and when it was set
- `muted`: Whether reactions are suppressed
- `native_rarity`, `native_stats`: Base data from bones (0-100 scale)
- `stats`: Trained TUI stats (0-255 scale, capped by rarity)
- `level`, `xp`, `title`, `stage`: Progression
