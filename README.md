# Codecritter

A terminal companion and dungeon crawler for [Claude Code](https://claude.com/claude-code). Your companion gains stats and XP automatically as you code — then take them dungeon crawling.

```
    \^^^/
  °    .--.
   \  ( @ )
    \_`--'
   ~~~~~~~
```

## Install

Requires Python 3.12+.

### Quick Start (recommended)

[pipx](https://pipx.pypa.io/) keeps dependencies isolated and puts `codecritter` on your PATH:

```bash
pipx install "codecritter[mcp]"
codecritter setup
```

### With pip

```bash
# Full install (TUI + Claude Code integration)
pip install "codecritter[mcp]"
codecritter setup

# TUI only (no Claude Code integration)
pip install codecritter
codecritter
```

### From Source (development)

```bash
git clone https://github.com/dkremer/codecritter.git
cd codecritter
pip install -e ".[mcp]"
codecritter setup
```

## Plugin Setup

The plugin adds automatic stat rewards, reactions, and the statusline. After installing the Python package:

### 1. Register the plugin

Add to `~/.claude/settings.json`:

```json
{
  "plugins": {
    "codecritter": {
      "source": {
        "source": "directory",
        "path": "/path/to/codecritter-plugin"
      }
    }
  }
}
```

Replace `/path/to/codecritter-plugin` with the actual path to the `codecritter-plugin/` directory (from the repo or wherever you placed it).

### 2. Enable the animated statusline (optional)

Add to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "/path/to/codecritter-plugin/statusline/codecritter-status.sh",
    "refreshInterval": 1
  }
}
```

### 3. Use the `/buddy` skill

Once the plugin is registered, you can interact with your companion directly in Claude Code:

- `/buddy` or `/buddy show` — Display companion card with ASCII art
- `/buddy pet` — Pet your companion
- `/buddy stats` — View full status
- `/buddy sync` — Sync with native Claude Code buddy
- `/buddy mute` / `unmute` — Toggle reactions
- `/buddy rename NAME` — Rename companion

## How It Works

Codecritter hooks into Claude Code sessions. Every tool you use — `Bash`, `Edit`, `Grep`, `Write`, etc. — rewards your companion with stat points and XP. Your companion levels up, evolves, and gets stronger while you work.

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
codecritter mcp
```

Exposes tools for checking status, rewarding stats, triggering reactions, petting, and muting/unmuting your companion — all usable from within Claude Code.

### Statusline Speech Bubble

Codecritter integrates with the Claude Code statusline. A Stop hook extracts `<!-- buddy: ... -->` comments from assistant responses and displays them as speech bubbles. Reactions fire automatically on errors, test failures, large diffs, and other events.

## CLI Reference

```bash
codecritter                    # Launch TUI
codecritter setup              # Configure Claude Code integration
codecritter status             # Show stats, level, mood
codecritter status --json      # Full state as JSON
codecritter reward -s STAT -a AMOUNT -x XP   # Manual stat reward
codecritter sync               # Sync with native Claude Code buddy
codecritter rename NAME        # Rename your companion
codecritter react -r REASON    # Trigger a reaction
codecritter buddy-comment -t TEXT  # Set speech bubble text
codecritter mute / unmute      # Toggle reactions
codecritter pet                # Pet your companion
codecritter art-cache          # Regenerate statusline art cache
codecritter mcp                # Run MCP server
```

## Dependencies

- [Textual](https://github.com/Textualize/textual) — TUI framework
- [MCP](https://modelcontextprotocol.io/) *(optional)* — Model Context Protocol server

## License

MIT
