# Jamb

A TUI dungeon crawler and companion system for [Claude Code](https://claude.com/claude-code). Your companion gains stats and XP automatically as you code — then take them dungeon crawling.

```
    \^^^/
  °    .--.
   \  ( @ )
    \_`--'
   ~~~~~~~
```

## Install

```bash
pip install jamb
```

For MCP server support:

```bash
pip install "jamb[mcp]"
```

Requires Python 3.12+.

## Quick Start

```bash
# Launch the TUI
jamb

# Check companion status
jamb status

# Run the MCP server for Claude Code
jamb mcp
```

## How It Works

Jamb hooks into Claude Code sessions. Every tool you use — `Bash`, `Edit`, `Grep`, `Write`, etc. — rewards your companion with stat points and XP. Your companion levels up, evolves, and gets stronger while you work.

### Hook Rewards

| Tool | Stat | XP |
|------|------|----|
| Bash | +1 debugging | +2 |
| Edit | +1 patience | +2 |
| Write | +1 wisdom | +2 |
| Agent | +1 chaos | +2 |
| Grep | +1 snark | +2 |
| Glob | +1 snark | +1 |
| Read | +1 wisdom | +1 |

Session start grants +5 XP. Session end rewards +2 patience and syncs progression.

## TUI

The terminal interface lets you view your companion, explore dungeons, manage inventory, and buy items.

### Keybindings

| Key | Action |
|-----|--------|
| `d` | Enter dungeon |
| `i` | Inventory |
| `s` | Shop |
| `q` | Quit |

## Dungeon

Procedurally generated floors with turn-based combat. Rooms contain enemies, treasure, traps, and bosses. Enemies are programming-themed — Null Pointer, Race Condition, Deadlock, Memory Leak, Infinite Loop, and more.

### Combat Type Wheel

A 5-way effectiveness system (1.5x strong, 0.5x weak):

```
debugging -> chaos -> patience -> snark -> wisdom -> debugging
```

Equipment (weapons, armor, accessories) and consumables add strategic depth.

## Species

18 companion species, deterministically assigned from your Claude Code account:

duck, goose, blob, cat, dragon, octopus, owl, penguin, turtle, snail, ghost, axolotl, capybara, cactus, robot, rabbit, mushroom, chonk

Each has unique ASCII art across three evolution stages (hatchling, juvenile, adult) with species-specific reactions and personality.

## Stats & Progression

Five stats on a 0-255 scale:

- **DEBUGGING** — Bug identification and fixing
- **PATIENCE** — Careful, methodical work
- **CHAOS** — Creative and unpredictable approaches
- **WISDOM** — Knowledge gathering and teaching
- **SNARK** — Pattern matching and witty responses

### Rarity

Rarity is determined by your account and sets progression caps:

| Rarity | Level Cap | Stat Cap |
|--------|-----------|----------|
| Common | 20 | 150 |
| Uncommon | 30 | 180 |
| Rare | 50 | 220 |
| Epic | 75 | 245 |
| Legendary | 100 | 255 |

### Evolution

Companions evolve through three stages as they level up:

- **Hatchling** (Level 1)
- **Juvenile** (Level 10)
- **Adult** (Level 20+)

## Shop

A daily rotating inventory of weapons, armor, consumables, and stat boosters. Higher-tier items unlock as your companion levels up.

## Claude Code Integration

### MCP Server

```bash
jamb mcp
```

Exposes tools for checking status, rewarding stats, triggering reactions, petting, and muting/unmuting your companion — all usable from within Claude Code.

### Statusline Speech Bubble

Jamb integrates with the Claude Code statusline. A Stop hook extracts `<!-- buddy: ... -->` comments from assistant responses and displays them as speech bubbles. Reactions fire automatically on errors, test failures, large diffs, and other events.

### Buddy Skill

The `/buddy` skill routes commands to MCP tools:

- `/buddy show` — Display companion card
- `/buddy pet` — Pet your companion
- `/buddy stats` — View full status
- `/buddy sync` — Sync with native buddy
- `/buddy mute` / `unmute` — Toggle reactions
- `/buddy rename NAME` — Rename companion

## CLI Reference

```bash
jamb                    # Launch TUI
jamb status             # Show stats, level, mood
jamb status --json      # Full state as JSON
jamb reward -s STAT -a AMOUNT -x XP   # Manual stat reward
jamb sync               # Sync with native Claude Code buddy
jamb react -r REASON    # Trigger a reaction
jamb buddy-comment -t TEXT  # Set speech bubble text
jamb mute / unmute      # Toggle reactions
jamb pet                # Pet your companion
jamb mcp                # Run MCP server
```

## Dependencies

- [Textual](https://github.com/Textualize/textual) — TUI framework
- [MCP](https://modelcontextprotocol.io/) *(optional)* — Model Context Protocol server

## License

MIT
