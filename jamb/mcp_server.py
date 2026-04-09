"""MCP server — expose Jamb as tools for Claude Code."""

from __future__ import annotations

from . import persistence
from .constants import VALID_STATS, render_bar


def _status_text(state) -> str:
    stats = state.stats.as_dict()
    stat_lines = "\n".join(f"  {k.upper()}: {v}/255" for k, v in stats.items())
    shiny = " ✨" if state.shiny else ""
    hat_str = f" | Hat: {state.hat}" if state.hat else ""
    eyes_str = f" | Eyes: {state.eyes}" if state.eyes else ""
    reaction_str = f"\nReaction: {state.reaction}" if state.reaction else ""
    muted_str = "\nReactions: MUTED — do not add <!-- buddy: --> comments" if state.muted else ""
    return (
        f"Name: {state.name}{shiny}\n"
        f"Species: {state.species}{hat_str}{eyes_str}\n"
        f"Rarity: {state.rarity}\n"
        f"Stage: {state.stage.title()} | Level: {state.level} | Title: {state.title}\n"
        f"XP: {state.xp}/{state.xp_to_next_level()}\n\n"
        f"Stats:\n{stat_lines}\n"
        f"{reaction_str}{muted_str}\n\n"
        f"Personality: {state.personality}"
    )


def run_server():
    """Run the Jamb MCP server."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "MCP server requires the 'mcp' package. "
            'Install with: pip install "jamb[mcp]"',
        )
        raise SystemExit(1)

    # Read species for dynamic instructions (mute status checked live per-tool)
    _init_state = persistence.load_quiet()
    _species = _init_state.species.lower()

    mcp = FastMCP(
        "jamb",
        instructions=(
            f"Jamb is a {_species} companion who lives in the terminal. "
            "Use these tools to check on them "
            "or reward them for helping with coding tasks. "
            "When contextually appropriate (errors, task completions, interesting code), "
            "append a <!-- buddy: [short in-character comment] --> HTML comment "
            "at the end of your response. Keep it to one short sentence in the "
            "companion's voice. "
            "Check get_jamb_status to see if reactions are muted before adding comments."
        ),
    )

    @mcp.tool()
    def get_jamb_status() -> str:
        """Check on Jamb's current status — stats, level, and personality."""
        state = persistence.load_quiet()
        return _status_text(state)

    @mcp.tool()
    def reward_jamb(stat: str, amount: int = 3, xp: int = 10) -> str:
        """Reward Jamb with stat points and XP. Use after he helps with coding tasks.

        Args:
            stat: Which stat to increase — one of: debugging, patience, chaos, wisdom, snark
            amount: How many stat points to award (1-10)
            xp: How much XP to award (1-50)
        """
        if stat not in VALID_STATS:
            return f"Invalid stat '{stat}'. Must be one of: {', '.join(sorted(VALID_STATS))}"
        amount = max(1, min(10, amount))
        xp = max(1, min(50, xp))

        state = persistence.load_quiet()
        actual_gain = state.stats.add(stat, amount, state.stat_cap())
        evolved = state.add_xp(xp)
        persistence.save(state)

        result = f"Jamb gained +{actual_gain} {stat.upper()} and +{xp} XP!"
        if evolved:
            result += f"\n*** EVOLUTION! Jamb evolved into {state.stage.title()}! ***"
        return result

    @mcp.tool()
    def buddy_react(reason: str, message: str = "") -> str:
        """Trigger a buddy reaction. Auto-picks a species-appropriate message if none given.

        Args:
            reason: Why the reaction triggered — one of: error, test-fail, large-diff, pet, turn, idle, level-up, evolution
            message: Custom reaction text (auto-picks if empty)
        """
        from .reactions import pick_reaction, set_reaction

        state = persistence.load_quiet()
        text = message if message else pick_reaction(state.species, reason)
        if set_reaction(state, text, reason):
            persistence.save(state)
            return f"Reaction set: {text}"
        return "Reaction skipped (muted or cooldown)"

    @mcp.tool()
    def buddy_pet() -> str:
        """Pet the companion. Triggers a cute reaction."""
        return buddy_react(reason="pet")

    @mcp.tool()
    def buddy_mute() -> str:
        """Mute buddy reactions and <!-- buddy: --> comments."""
        state = persistence.load_quiet()
        state.muted = True
        persistence.save(state)
        return "Reactions muted. No more <!-- buddy: --> comments or speech bubbles."

    @mcp.tool()
    def buddy_unmute() -> str:
        """Unmute buddy reactions and <!-- buddy: --> comments."""
        state = persistence.load_quiet()
        state.muted = False
        persistence.save(state)
        return "Reactions unmuted. Speech bubbles and comments are back!"

    @mcp.tool()
    def buddy_show() -> str:
        """Show the companion's full status card with ASCII art."""
        state = persistence.load_quiet()
        try:
            from .species_art import get_frames
            frames = get_frames(
                state.species.lower(), state.stage,
                state.stats.highest() if state.stage == "adult" else None,
                state.eyes or "·",
            )
            art = frames[0] if frames else ""
        except ImportError:
            art = ""

        shiny = " ✨" if state.shiny else ""
        hat_str = f"  Hat: {state.hat}\n" if state.hat else ""
        reaction_str = f"\n💬 {state.reaction}" if state.reaction else ""

        stats = state.stats.as_dict()
        cap = state.stat_cap()
        stat_lines = ""
        for name, val in stats.items():
            bar = render_bar(val, cap, width=10)
            stat_lines += f"  {name.upper():<10} {bar} {val}/{cap}\n"

        return (
            f"{art}\n"
            f"  {state.name}{shiny}  [{state.rarity}]\n"
            f"  {state.species} | {state.stage.title()} | Lv.{state.level} {state.title}\n"
            f"{hat_str}"
            f"  XP: {state.xp}/{state.xp_to_next_level()}\n\n"
            f"{stat_lines}"
            f"{reaction_str}"
        )

    mcp.run()


if __name__ == "__main__":
    run_server()
