"""Reaction system — species-specific speech bubbles and event reactions.

Ported from claude-buddy's reactions.ts, extended for Codecritter's care/progression.
"""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import CodecritterState


# ── Cooldowns (seconds) ────────────────────────────────────────────
# NOTE: The bash hooks (react.sh, buddy-comment.sh) duplicate these
# values as a fast-path check to avoid spawning Python. Keep in sync.

COOLDOWNS: dict[str, float] = {
    "error": 15.0,
    "test-fail": 15.0,
    "large-diff": 15.0,
    "buddy-comment": 2.0,
    "pet": 5.0,
    "turn": 5.0,
    "idle": 30.0,
    "hatch": 0.0,
    "level-up": 0.0,
    "evolution": 0.0,
}

# ── General Reaction Pools ─────────────────────────────────────────

GENERAL_REACTIONS: dict[str, list[str]] = {
    "hatch": [
        "*blinks* ...where am I?",
        "*stretches* hello, world!",
        "*looks around* this terminal is cozy.",
        "*yawns* did I just boot up?",
    ],
    "pet": [
        "*happy noises*",
        "*purrs contentedly*",
        "*nuzzles your cursor*",
        "*wiggles with joy*",
        "...do that again.",
        "*leans into it*",
    ],
    "error": [
        "*head tilts* ...that doesn't look right.",
        "saw that one coming.",
        "*adjusts glasses* line {line}, maybe?",
        "oof. that's a spicy error.",
        "*winces* been there.",
        "classic.",
    ],
    "test-fail": [
        "*slow blink* ...that test.",
        "bold of you to assume that would pass.",
        "*taps clipboard* {count} failed.",
        "have you tried... writing the code correctly?",
        "red means stop. and also cry.",
        "*takes notes*",
    ],
    "large-diff": [
        "that's... a lot of changes.",
        "*counts lines* are you refactoring or rewriting?",
        "*nervous laughter* {lines} lines changed.",
        "bold. very bold.",
        "I hope you tested that.",
    ],
    "turn": [
        "*watches quietly*",
        "*takes notes*",
        "*nods*",
        "...",
        "*adjusts hat*",
    ],
    "idle": [
        "*dozes off*",
        "*doodles in margins*",
        "*stares at cursor blinking*",
        "zzz...",
    ],
    "level-up": [
        "LEVEL UP! *sparkles everywhere*",
        "*glows with power* New level unlocked!",
        "I feel... stronger!",
        "*flexes* is this what leveling feels like?",
    ],
    "evolution": [
        "WHAT'S HAPPENING?! *blinding light*",
        "I'm... EVOLVING!",
        "*dramatic transformation sequence*",
        "This isn't even my final form!",
    ],
}

# ── Species-Specific Overrides ─────────────────────────────────────
# 40% chance to use these when available for the species+reason combo.

SPECIES_REACTIONS: dict[str, dict[str, list[str]]] = {
    "owl": {
        "error": [
            "*head rotates 180°* I saw that.",
            "*unblinking stare* check your types.",
            "who? who wrote this bug? ...you did.",
        ],
        "pet": [
            "*ruffles feathers* ...acceptable.",
            "*hoots softly*",
        ],
        "test-fail": [
            "*blinks slowly* I saw that coming.",
            "*rotates head* ...fascinating failure.",
        ],
        "idle": [
            "*watches from the shadows*",
            "*silent judgment*",
        ],
    },
    "cat": {
        "error": [
            "*knocks error off table*",
            "*licks paw, ignoring the stacktrace*",
            "*pushes the bug off the screen*",
        ],
        "pet": [
            "*purrs* ...don't let it go to your head.",
            "*head bumps the cursor*",
            "*kneads keyboard* my turn.",
        ],
        "idle": [
            "*knocks something off the status bar*",
            "*sits on your code* this is mine now.",
        ],
    },
    "duck": {
        "error": [
            "*quacks at the bug*",
            "have you tried rubber duck debugging? oh wait.",
            "QUACK! That's definitely wrong.",
        ],
        "pet": [
            "*happy quacking*",
            "*waddles in circles*",
        ],
        "test-fail": [
            "*quacks disapprovingly*",
            "duck duck... FAIL.",
        ],
    },
    "dragon": {
        "error": [
            "*smoke curls from nostrils*",
            "*contemplates burning it all down*",
            "I could just... incinerate the codebase.",
        ],
        "large-diff": [
            "*breathes fire on the old code* good riddance.",
            "a worthy refactor. I approve.",
        ],
        "pet": [
            "*smoke ring of contentment*",
            "*rumbles happily*",
        ],
    },
    "ghost": {
        "error": [
            "*phases through the stack trace*",
            "I've seen worse... in the afterlife.",
            "this code is haunted. trust me, I know haunted.",
        ],
        "idle": [
            "*haunts your unused imports*",
            "*phases in and out of existence*",
        ],
        "pet": [
            "*your hand passes through* ...it's the thought that counts.",
            "*flickers warmly*",
        ],
    },
    "robot": {
        "error": [
            "SYNTAX. ERROR. DETECTED.",
            "*beeps aggressively*",
            "ERROR LOGGED. DISAPPOINTMENT REGISTERED.",
        ],
        "test-fail": [
            "FAILURE RATE: UNACCEPTABLE.",
            "RUNNING DIAGNOSTIC... DIAGNOSIS: SKILL ISSUE.",
        ],
        "pet": [
            "AFFECTION ACKNOWLEDGED. GRATITUDE SUBROUTINE RUNNING.",
            "*whirrs contentedly*",
        ],
    },
    "axolotl": {
        "error": [
            "*regenerates your hope*",
            "*wiggles gills sympathetically*",
        ],
        "pet": [
            "*happy gill wiggle*",
            "*blushes pink*",
            "*does a little spin*",
        ],
    },
    "capybara": {
        "error": [
            "*unbothered* it'll be fine.",
            "*chilling* bugs happen. relax.",
        ],
        "pet": [
            "*maximum chill achieved*",
            "*closes eyes in bliss*",
        ],
        "idle": [
            "*just sits there, radiating calm*",
            "*vibing*",
        ],
    },
    "snail": {
        "error": [
            "*retreats into shell* ...that was bad.",
            "*leaves a trail of sad slime*",
        ],
        "pet": [
            "*wiggles antennae happily*",
            "*leaves a glitter trail*",
        ],
        "idle": [
            "*slowly crosses the terminal*",
            "*munches on a deprecated function*",
        ],
    },
}


def pick_reaction(species: str, reason: str, **kwargs: str) -> str:
    """Pick a reaction message, with species-specific override chance.

    Args:
        species: The companion's species (e.g., "Duck", "Snail").
        reason: Why the reaction triggered (e.g., "error", "pet").
        **kwargs: Template substitutions ({line}, {count}, {lines}).
    """
    key = species.lower()
    pool = GENERAL_REACTIONS.get(reason, ["..."])

    # 40% chance for species-specific
    if key in SPECIES_REACTIONS:
        sp_pool = SPECIES_REACTIONS[key].get(reason)
        if sp_pool and random.random() < 0.4:
            pool = sp_pool

    msg = random.choice(pool)
    for k, v in kwargs.items():
        msg = msg.replace(f"{{{k}}}", str(v))
    return msg


def set_reaction(state: CodecritterState, text: str, reason: str) -> bool:
    """Set a reaction on the state, respecting mute and cooldowns.

    Returns True if the reaction was set, False if skipped.
    """
    if state.muted:
        return False

    now = time.time()
    cooldown = COOLDOWNS.get(reason, 10.0)

    if state.reaction_ts is not None:
        elapsed = now - state.reaction_ts
        if elapsed < cooldown:
            return False

    state.reaction = text
    state.reaction_reason = reason
    state.reaction_ts = now
    return True
