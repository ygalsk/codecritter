"""CLI commands for Codecritter — reward, status, and MCP server."""

from __future__ import annotations

import argparse
import json
import sys

from . import persistence
from .constants import VALID_STATS, render_bar


def cmd_reward(args: argparse.Namespace) -> None:
    """Reward Jamb with stat points and XP."""
    if args.stat not in VALID_STATS:
        print(f"Invalid stat '{args.stat}'. Must be one of: {', '.join(sorted(VALID_STATS))}")
        sys.exit(1)

    state = persistence.load_quiet()
    actual_gain = state.stats.add(args.stat, args.amount, state.stat_cap())
    evolved = state.add_xp(args.xp)
    persistence.save(state)

    print(f"Jamb gained +{actual_gain} {args.stat.upper()} and +{args.xp} XP!")
    if evolved:
        print(f"*** EVOLUTION! Jamb evolved into {state.stage.title()}! ***")


def cmd_status(args: argparse.Namespace) -> None:
    """Print Jamb's current status."""
    state = persistence.load_quiet()
    stats = state.stats.as_dict()

    cap = state.stat_cap()
    print(f"{state.name}  [{state.rarity}]")
    print(f"Stage: {state.stage.title()} | Level: {state.level}/{state.level_cap()} | Title: {state.title}")
    print(f"XP: {state.xp}/{state.xp_to_next_level()}")
    print()
    native = state.native_stats or {}
    for name, val in stats.items():
        bar = render_bar(val, cap, width=20)
        base = native.get(name)
        base_str = f"  (base: {base})" if base is not None else ""
        print(f"  {name.upper():<10} {bar} {val}/{cap}{base_str}")
    print()
    if not state.bones_synced:
        print("  ⚠ Native bones not synced yet. Run: codecritter sync")

    if args.json:
        print()
        print(json.dumps(state.as_dict(), indent=2))


def cmd_sync(args: argparse.Namespace) -> None:
    """Bidirectional sync between native buddy and TUI."""
    from .sync import full_sync

    state = persistence.load_quiet()
    result = full_sync(state)
    persistence.save(state)

    if result["bones_to_tui"]:
        print(f"Native → TUI: Synced rarity={state.native_rarity}, base stats={state.native_stats}")
        print(f"  Rarity display: {state.rarity}")
        print(f"  Level cap: {state.level_cap()}, Stat cap: {state.stat_cap()}")
    else:
        print("Native → TUI: Could not read native bones (missing ~/.claude.json or org UUID)")

    if result["tui_to_native"]:
        print(f"TUI → Native: Pushed Lv{state.level} {state.title} to .claude.json personality")
    else:
        print("TUI → Native: Could not update .claude.json")


def cmd_session_end(args: argparse.Namespace) -> None:
    """Session end: reward patience + sync to native."""
    from .sync import sync_tui_to_native

    state = persistence.load_quiet()
    actual_gain = state.stats.add("patience", 2, state.stat_cap())
    state.add_xp(5)
    sync_tui_to_native(state)
    persistence.save(state)

    print(f"Session end: +{actual_gain} PATIENCE, +5 XP. Synced to native.")


def cmd_react(args: argparse.Namespace) -> None:
    """Set a reaction on Jamb (used by hooks)."""
    from .reactions import pick_reaction, set_reaction

    state = persistence.load_quiet()
    if args.message:
        text = args.message
    else:
        text = pick_reaction(state.species, args.reason)
    if set_reaction(state, text, args.reason):
        persistence.save(state)
        print(f"Reaction set: {text}")
    else:
        print("Reaction skipped (muted or cooldown)")


def cmd_buddy_comment(args: argparse.Namespace) -> None:
    """Set a reaction from an extracted <!-- buddy: ... --> comment."""
    from .reactions import set_reaction

    state = persistence.load_quiet()
    if set_reaction(state, args.text, "buddy-comment"):
        persistence.save(state)
        print(f"Buddy comment set: {args.text}")
    else:
        print("Comment skipped (muted or cooldown)")


def cmd_mute(args: argparse.Namespace) -> None:
    """Mute buddy reactions."""
    state = persistence.load_quiet()
    state.muted = True
    persistence.save(state)
    print("Reactions muted.")


def cmd_unmute(args: argparse.Namespace) -> None:
    """Unmute buddy reactions."""
    state = persistence.load_quiet()
    state.muted = False
    persistence.save(state)
    print("Reactions unmuted.")


def cmd_pet(args: argparse.Namespace) -> None:
    """Pet the companion."""
    from .reactions import pick_reaction, set_reaction

    state = persistence.load_quiet()
    text = pick_reaction(state.species, "pet")
    if set_reaction(state, text, "pet"):
        persistence.save(state)
        print(text)
    else:
        print("Reaction skipped (muted or cooldown)")


def cmd_art_cache(args: argparse.Namespace) -> None:
    """Regenerate the art cache for the statusline."""
    from .art_cache import write_art_cache

    state = persistence.load_quiet()
    write_art_cache(state)
    print("Art cache updated.")


def cmd_rename(args: argparse.Namespace) -> None:
    """Rename the companion."""
    state = persistence.load_quiet()
    state.name = args.name
    persistence.save(state)
    print(f"Renamed to {state.name}")


def cmd_hook_react(args: argparse.Namespace) -> None:
    """Hook handler: detect errors/test-fails/large-diffs from stdin JSON."""
    from .hook_handlers import handle_react
    handle_react()


def cmd_hook_comment(args: argparse.Namespace) -> None:
    """Hook handler: extract <!-- buddy: --> comments from stdin JSON."""
    from .hook_handlers import handle_comment
    handle_comment()


def cmd_setup(args: argparse.Namespace) -> None:
    """Configure Claude Code integration."""
    from .setup import run_setup
    run_setup()


def cmd_mcp(args: argparse.Namespace) -> None:
    """Run the MCP server."""
    from .mcp_server import run_server
    run_server()


def cli_main() -> None:
    """Entry point for `codecritter` CLI with subcommands."""
    parser = argparse.ArgumentParser(
        prog="codecritter",
        description="Codecritter — your terminal companion",
    )
    sub = parser.add_subparsers(dest="command")

    # reward
    reward_p = sub.add_parser("reward", help="Reward Jamb with stat points and XP")
    reward_p.add_argument("--stat", "-s", required=True, help="Stat to increase")
    reward_p.add_argument("--amount", "-a", type=int, default=3, help="Stat points (1-10)")
    reward_p.add_argument("--xp", "-x", type=int, default=10, help="XP to award (1-50)")

    # status
    status_p = sub.add_parser("status", help="Print Jamb's current status")
    status_p.add_argument("--json", action="store_true", help="Also output raw JSON")

    # sync
    sub.add_parser("sync", help="Sync native buddy bones with TUI (bidirectional)")

    # session-end
    sub.add_parser("session-end", help="End session: reward + sync to native buddy")

    # react
    react_p = sub.add_parser("react", help="Set a reaction (used by hooks)")
    react_p.add_argument("--reason", "-r", required=True, help="Reaction reason (error, test-fail, large-diff, etc.)")
    react_p.add_argument("--message", "-m", help="Custom reaction message (auto-picks if omitted)")

    # buddy-comment
    bc_p = sub.add_parser("buddy-comment", help="Set reaction from extracted <!-- buddy: --> comment")
    bc_p.add_argument("--text", "-t", required=True, help="Extracted comment text")

    # mute / unmute
    sub.add_parser("mute", help="Mute buddy reactions")
    sub.add_parser("unmute", help="Unmute buddy reactions")

    # pet
    sub.add_parser("pet", help="Pet the companion")

    # art-cache
    sub.add_parser("art-cache", help="Regenerate statusline art cache")

    # rename
    rename_p = sub.add_parser("rename", help="Rename your companion")
    rename_p.add_argument("name", help="New name for the companion")

    # hook-react
    sub.add_parser("hook-react", help="Hook handler: detect errors/test-fails from stdin")

    # hook-comment
    sub.add_parser("hook-comment", help="Hook handler: extract buddy comments from stdin")

    # setup
    sub.add_parser("setup", help="Configure Claude Code integration")

    # mcp
    sub.add_parser("mcp", help="Run MCP server for Claude Code integration")

    args = parser.parse_args()

    if args.command == "reward":
        cmd_reward(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "sync":
        cmd_sync(args)
    elif args.command == "session-end":
        cmd_session_end(args)
    elif args.command == "react":
        cmd_react(args)
    elif args.command == "buddy-comment":
        cmd_buddy_comment(args)
    elif args.command == "mute":
        cmd_mute(args)
    elif args.command == "unmute":
        cmd_unmute(args)
    elif args.command == "pet":
        cmd_pet(args)
    elif args.command == "art-cache":
        cmd_art_cache(args)
    elif args.command == "rename":
        cmd_rename(args)
    elif args.command == "hook-react":
        cmd_hook_react(args)
    elif args.command == "hook-comment":
        cmd_hook_comment(args)
    elif args.command == "setup":
        cmd_setup(args)
    elif args.command == "mcp":
        cmd_mcp(args)
    else:
        # No subcommand — launch TUI
        from .app import CodecritterApp
        CodecritterApp().run()
