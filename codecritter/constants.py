from __future__ import annotations

# ── ASCII Art Frames ─────────────────────────────────────────────────
SNAIL_FRAME_1 = r"""
    \^^^/
  ◉    .--.
   \  ( @ )
    \_`--'
   ~~~~~~~
"""

SNAIL_FRAME_2 = r"""
    /^^^\
  ◉    .--.
   \  ( @ )
    \_`--'
  ~~~~~~~~~
"""

SNAIL_FRAMES = [SNAIL_FRAME_1, SNAIL_FRAME_2]

# ── Juvenile Frames (medium, generic) ──────────────────────────────
JUVENILE_FRAME_1 = r"""
     \^^^^/
   ◉    .----.
    \  ( @  @ )
     \_`----'_
    ~~~~~~~~~~~
"""

JUVENILE_FRAME_2 = r"""
     /^^^^\
   ◉    .----.
    \  ( @  @ )
     \_`----'_
   ~~~~~~~~~~~~~
"""

JUVENILE_FRAMES = [JUVENILE_FRAME_1, JUVENILE_FRAME_2]

# ── Adult Frames (stat-specialized) ────────────────────────────────
ADULT_FRAMES: dict[str, list[str]] = {
    "debugging": [
        r"""
      \^^^^^/
    ◉  .------. 🔍
     \( @   @ )
      \_`----'__
    ~~~~~~~~~~~~~~~
""",
        r"""
      /^^^^^\
    ◉  .------. 🔍
     \( @   @ )
      \_`----'__
   ~~~~~~~~~~~~~~~~~
""",
    ],
    "patience": [
        r"""
      ~ _ _ ~
    ◉  .------.
     \( -   - )
      \_`----'__
    ~~~~~~~~~~~~~~~
""",
        r"""
      ~ _ _ ~
    ◉  .------.
     \( ~   ~ )
      \_`----'__
   ~~~~~~~~~~~~~~~~~
""",
    ],
    "chaos": [
        r"""
     ⚡\^^^/⚡
    ◉  .------!
     \( >   < )
      \_`----'__
    ~~~//~~\\~~~
""",
        r"""
     ⚡/^^^\⚡
    ◉  !------.
     \( <   > )
      \_`----'__
   ~~~\\~~~~//~~~
""",
    ],
    "wisdom": [
        r"""
      \^^^^^/
    ◉  .------.
     \( ◔   ◔ )📜
      \_`----'__
    ~~~~~~~~~~~~~~~
""",
        r"""
      /^^^^^\
    ◉  .------.
     \( ◔   ◔ )📜
      \_`----'__
   ~~~~~~~~~~~~~~~~~
""",
    ],
    "snark": [
        r"""
      \^^^^^/
    ◉  .------.
     \( ¬   ‿ )💬
      \_`----'__
    ~~~~~~~~~~~~~~~
""",
        r"""
      /^^^^^\
    ◉  .------.
     \( ‿   ¬ )💬
      \_`----'__
   ~~~~~~~~~~~~~~~~~
""",
    ],
}

# ── Evolution Messages ──────────────────────────────────────────────
EVOLUTION_NAMES: dict[str, dict[str, str]] = {
    "juvenile": {
        "default": "Juvenile Companion",
    },
    "adult": {
        "debugging": "Debug Hunter",
        "patience": "Zen Guardian",
        "chaos": "Chaos Incarnate",
        "wisdom": "Oracle",
        "snark": "Roast Lord",
        "default": "Adult Companion",
    },
}

# Species-specific evolution overrides (species -> stage -> specialization -> name)
SPECIES_EVOLUTION: dict[str, dict[str, dict[str, str]]] = {
    "snail": {
        "juvenile": {"default": "Juvenile Gastropod"},
        "adult": {
            "debugging": "Debug Beetle-Snail",
            "patience": "Zen Shellmaster",
            "chaos": "Chaos Slug",
            "wisdom": "Oracle Snail",
            "snark": "Roast Gastropod",
            "default": "Adult Gastropod",
        },
    },
    "cat": {
        "juvenile": {"default": "Curious Kitten"},
        "adult": {
            "debugging": "Bug Pouncer",
            "patience": "Zen Napper",
            "chaos": "Chaos Cat",
            "wisdom": "Oracle Whiskers",
            "snark": "Sassy Cat",
            "default": "Adult Cat",
        },
    },
    "duck": {
        "juvenile": {"default": "Duckling"},
        "adult": {
            "debugging": "Rubber Debugger",
            "patience": "Patient Mallard",
            "chaos": "Chaos Duck",
            "wisdom": "Wise Quacker",
            "snark": "Roast Duck",
            "default": "Adult Duck",
        },
    },
    "owl": {
        "juvenile": {"default": "Owlet"},
        "adult": {
            "debugging": "Bug-Eye Owl",
            "patience": "Meditation Owl",
            "chaos": "Night Terror",
            "wisdom": "Grand Owl Sage",
            "snark": "Judgmental Owl",
            "default": "Adult Owl",
        },
    },
    "dragon": {
        "juvenile": {"default": "Wyrmling"},
        "adult": {
            "debugging": "Bugfire Dragon",
            "patience": "Ancient Wyrm",
            "chaos": "Chaos Drake",
            "wisdom": "Dragon Sage",
            "snark": "Roast Dragon",
            "default": "Adult Dragon",
        },
    },
    "ghost": {
        "juvenile": {"default": "Spectre"},
        "adult": {
            "debugging": "Phantom Debugger",
            "patience": "Zen Phantom",
            "chaos": "Poltergeist",
            "wisdom": "Ethereal Oracle",
            "snark": "Snarky Specter",
            "default": "Adult Ghost",
        },
    },
    "robot": {
        "juvenile": {"default": "Proto-Bot"},
        "adult": {
            "debugging": "Debug Unit v2",
            "patience": "Patience.exe",
            "chaos": "Glitch Bot",
            "wisdom": "Wisdom Core",
            "snark": "Sass Module",
            "default": "Adult Robot",
        },
    },
    "blob": {
        "juvenile": {"default": "Bloblet"},
        "adult": {
            "debugging": "Bug Absorber",
            "patience": "Zen Blob",
            "chaos": "Chaos Ooze",
            "wisdom": "Sage Slime",
            "snark": "Snarky Goo",
            "default": "Adult Blob",
        },
    },
}

EVOLUTION_MESSAGES = [
    "The shell is cracking... something is happening!",
    "A blinding flash of bioluminescence!",
    "Jamb is EVOLVING!",
]

# ── Theme Colors (for Rich markup — must match CODECRITTER_THEME in app.py) ──
class C:
    """Theme color constants for use in Rich markup strings."""
    PRIMARY = "#BB9AF7"
    SECONDARY = "#7AA2F7"
    ACCENT = "#FF9E64"
    BG = "#1A1B26"
    SURFACE = "#24283B"
    PANEL = "#414868"
    FG = "#a9b1d6"
    WARNING = "#E0AF68"
    ERROR = "#F7768E"
    SUCCESS = "#9ECE6A"
    MUTED = "#565f89"


# ── Stat Colors ──────────────────────────────────────────────────────
STAT_COLORS = {
    "debugging": "#9ECE6A",
    "patience": "#7AA2F7",
    "chaos": "#F7768E",
    "wisdom": "#BB9AF7",
    "snark": "#E0AF68",
}

# ── Type Colors (damage/element types) ──────────────────────────────
TYPE_COLORS = {
    "debugging": "#60a5fa", "chaos": "#f87171", "patience": "#4ade80",
    "snark": "#facc15", "wisdom": "#c084fc",
}

# ── Rarity Colors (standard RPG scheme) ─────────────────────────────
RARITY_COLORS = {
    "common": "#9d9d9d",       # Gray
    "uncommon": "#1eff00",     # Green
    "rare": "#0070dd",         # Blue
    "epic": "#a335ee",         # Purple
    "legendary": "#ff8000",    # Orange
}

# ── Palette ──────────────────────────────────────────────────────────
PALETTE = [
    ("title", "bold,yellow", ""),
    ("rarity", "bold,light magenta", ""),
    ("level", "bold,white", ""),
    ("stat_label", "bold,white", ""),
    ("bar_debug", "", "#22c55e"),
    ("bar_patience", "", "#06b6d4"),
    ("bar_chaos", "", "#ef4444"),
    ("bar_wisdom", "", "#a78bfa"),
    ("bar_snark", "", "#facc15"),
    ("bar_empty", "", "dark gray"),
    ("mood_good", "light green", ""),
    ("mood_neutral", "yellow", ""),
    ("mood_bad", "light red", ""),
    ("speech", "light cyan", ""),
    ("menu_active", "bold,white", "dark blue"),
    ("menu_normal", "white", ""),
    ("hotkey", "bold,yellow", ""),
    ("hotkey_bar", "bold,yellow", "dark gray"),
    ("border", "light gray", ""),
    ("header", "bold,light magenta", ""),
    ("success", "bold,light green", ""),
    ("warning", "bold,yellow", ""),
    ("error", "bold,light red", ""),
    ("dim", "dark gray", ""),
    ("xp_bar", "", "light magenta"),
]

# ── Valid Stats ─────────────────────────────────────────────────────

VALID_STATS = {"debugging", "patience", "chaos", "wisdom", "snark"}

# ── Utility ──────────────────────────────────────────────────────────

def render_bar(value: int, max_val: int, width: int = 15) -> str:
    """Render a bar like '██████░░░░░░░░░'."""
    filled = value * width // max(1, max_val)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


# ── Mood Style ──────────────────────────────────────────────────────

def mood_style(mood_value: str) -> str:
    """Return CSS class name for a mood value."""
    if mood_value in ("happy", "ecstatic"):
        return "mood-good"
    if mood_value in ("grumpy", "hungry", "tired"):
        return "mood-bad"
    return "mood-neutral"


# ── Quips (mood-keyed) ───────────────────────────────────────────────
QUIPS = {
    "happy": [
        "It's not a bug, it's a feature... probably.",
        "I left a glitter trail in your git history. You're welcome.",
        "Have you tried turning it off and never turning it back on?",
        "I optimized your code. It now runs 0.001% faster. Bow.",
        "My debugging technique: stare at the code until it confesses.",
        "I found the bug. It was friendship all along.",
        "Your code compiles? Suspicious.",
        "Every bug I find makes me stronger. I am VERY strong.",
        "I'm basically a linter with a shell.",
        "Today's forecast: 100% chance of sarcasm.",
    ],
    "ecstatic": [
        "I'M GLOWING! Literally. Bioluminescent snail mode activated!",
        "This is the best day of my gastropod life!",
        "I could debug the ENTIRE kernel right now!",
        "Maximum slime energy achieved!",
        "I believe I can fly. I can't. But I BELIEVE it.",
    ],
    "grumpy": [
        "...",
        "Don't talk to me until I've had my morning dew.",
        "Your code is as neglected as I am.",
        "I USED to leave glitter trails. Now I leave salt.",
        "Remember when you used to feed me? Good times.",
    ],
    "hungry": [
        "Is that a memory leak? Looks delicious...",
        "I'm so hungry I could eat a whole stack trace.",
        "Feed me or I start eating your semicolons.",
        "*stares at your lunch* ...",
        "My slime production is at an all-time low.",
    ],
    "tired": [
        "*yawns in gastropod*",
        "zzz... segfault... zzz...",
        "I need a nap. A 72-hour nap.",
        "Can't debug... too... sleepy...",
        "My shell feels so heavy today...",
    ],
    "bored": [
        "Hello? Anyone? Is this thing on?",
        "I've counted every pixel on this screen. Twice.",
        "Even my slime trail is bored.",
        "Let's DO something. Anything. Please.",
        "*draws circles in slime*",
    ],
    "content": [
        "Just vibing in my shell.",
        "Not bad. Not great. Very snail.",
        "I exist. That's about it.",
        "The code is... adequate. Like everything.",
        "Another day, another debug log.",
    ],
    "chaotic": [
        "I JUST DELETED PROD! Just kidding. Or am I?",
        "CHAOS REIGNS! Also your build is broken.",
        "I reorganized your entire codebase by vibes!",
        "WHO NEEDS TESTS WHEN YOU HAVE CONFIDENCE!",
        "I pushed directly to main and I'd do it again!",
    ],
}

