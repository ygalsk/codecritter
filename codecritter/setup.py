"""Setup command — configure Codecritter for Claude Code integration."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import persistence
from .art_cache import write_art_cache

CODECRITTER_DIR = Path.home() / ".claude" / "codecritter"


def run_setup() -> None:
    """Configure Claude Code integration for Codecritter."""
    print("Setting up Codecritter...\n")

    # 1. Ensure save directory exists
    CODECRITTER_DIR.mkdir(parents=True, exist_ok=True)
    print("[1/4] Save directory ready: ~/.claude/codecritter/")

    # 2. Verify codecritter is on PATH
    codecritter_bin = shutil.which("codecritter")
    if codecritter_bin:
        print(f"[2/4] Found codecritter on PATH: {codecritter_bin}")
    else:
        print("[2/4] Warning: 'codecritter' not found on PATH.")
        print('       Make sure you installed with: pip install "codecritter[mcp]"')
        print("       If using pipx, ensure ~/.local/bin is on your PATH.")

    # 3. Initial sync
    try:
        from .sync import full_sync

        state = persistence.load_quiet()
        result = full_sync(state)
        persistence.save(state)
        if result["bones_to_tui"]:
            print(f"[3/4] Synced native bones: {state.species} ({state.rarity})")
        else:
            print("[3/4] Could not sync native bones (missing ~/.claude.json or org UUID)")
            print("       This is normal if you haven't used Claude Code yet.")
    except Exception as e:
        print(f"[3/4] Sync skipped: {e}")

    # 4. Bootstrap art cache
    try:
        state = persistence.load_quiet()
        write_art_cache(state)
        print("[4/4] Art cache bootstrapped.")
    except Exception as e:
        print(f"[4/4] Art cache skipped: {e}")

    # Done — print next steps
    print("\n" + "=" * 50)
    print("Setup complete!\n")
    print("Next steps:\n")

    print("1. Install the Claude Code plugin:")
    print("   Add to ~/.claude/settings.json under \"plugins\":")
    print('   "codecritter": {')
    print('     "source": {')
    print('       "source": "directory",')
    print('       "path": "<path-to-codecritter-plugin>"')
    print("     }")
    print("   }")
    print()
    print("2. Configure the statusline (optional):")
    print("   Add to ~/.claude/settings.json:")
    print('   "statusLine": {')
    print('     "type": "command",')
    print('     "command": "<path-to-codecritter-plugin>/statusline/codecritter-status.sh",')
    print('     "refreshInterval": 1')
    print("   }")
    print()
    print("3. Launch the TUI:")
    print("   codecritter")
