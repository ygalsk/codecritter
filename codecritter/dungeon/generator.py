"""Procedural dungeon floor generator."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field

from .enemies import boss_for_floor, enemies_for_floor


# Room types
EMPTY = "."
WALL = "#"
ENEMY = "!"
TREASURE = "?"
REST = "+"
TRAP = "^"
STAIRS = ">"
ENTRANCE = "@"
BOSS = "B"
# ── New room types ──────────────────────────────────────
SHOP = "$"
FORK = "Y"
EXTRACTION = "E"
CURSED_CHEST = "C"

ROOM_DESCRIPTIONS = {
    EMPTY: [
        "An empty server rack hums quietly.",
        "Stale coffee and scattered printouts.",
        "The fluorescent lights flicker overhead.",
        "Keyboard clacking echoes in the distance.",
        "A whiteboard covered in faded diagrams.",
    ],
    TRAP: [
        "The floor crackles with undefined behavior!",
        "A wild segfault appears from the shadows!",
        "You step on a deprecated API endpoint!",
        "A hidden TODO: fix this later strikes!",
    ],
    REST: [
        "A cozy break room with a working coffee machine.",
        "A quiet corner with a beanbag chair.",
        "A rubber duck meditation corner.",
    ],
    TREASURE: [
        "A dusty package.json with something shiny inside.",
        "An old deploy artifact with valuables.",
        "A forgotten stash of dev tools.",
    ],
    SHOP: [
        "A vendor sits behind a makeshift desk of stacked monitors.",
        "A traveling merchant offers wares from their cargo container.",
    ],
    FORK: [
        "The corridor splits into two paths.",
    ],
    EXTRACTION: [
        "A secure backup terminal hums with green light.",
        "An extraction point — bank your progress here.",
    ],
    CURSED_CHEST: [
        "A glowing chest pulses with unstable energy...",
        "A corrupted data archive. Open at your own risk.",
    ],
}

# Fork room options — pairs of (description, hidden_room_type)
FORK_OPTIONS = [
    ("You hear growling from the left", ENEMY),
    ("The right path smells of gold", TREASURE),
    ("A warm glow beckons left", REST),
    ("The right path crackles with energy", TRAP),
    ("Faint humming comes from the left", TREASURE),
    ("The right path is eerily silent", ENEMY),
]


@dataclass
class Room:
    x: int
    y: int
    room_type: str = EMPTY
    explored: bool = False
    enemy: dict | None = None
    loot: dict | None = None
    description: str = ""
    cleared: bool = False
    trap: dict | None = None  # biome trap data
    fork_options: list | None = None  # [(description, hidden_type), ...]

    def as_dict(self) -> dict:
        return {
            "x": self.x, "y": self.y,
            "room_type": self.room_type,
            "explored": self.explored,
            "enemy": self.enemy,
            "loot": self.loot,
            "description": self.description,
            "cleared": self.cleared,
            "trap": self.trap,
            "fork_options": self.fork_options,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Room:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Floor:
    number: int
    width: int = 5
    height: int = 5
    rooms: list[list[Room]] = field(default_factory=list)
    player_x: int = 0
    player_y: int = 0

    def generate(
        self,
        seed: int | None = None,
        biome: str = "generic",
        stats: dict | None = None,
        floor_modifier: dict | None = None,
    ) -> None:
        rng = random.Random(seed)
        stats = stats or {}

        # Load biome data for room descriptions and traps
        from . import data_loader
        biome_data = data_loader.load_biome(biome)
        biome_descs = biome_data.get("room_descriptions", {})
        biome_traps = biome_data.get("traps", [])
        biome_clues = biome_data.get("boss_clues", [])

        # Merge biome room descriptions with defaults
        room_descs = dict(ROOM_DESCRIPTIONS)
        for key, descs in biome_descs.items():
            symbol = _desc_key_to_symbol(key)
            if symbol and descs:
                room_descs[symbol] = descs

        self.rooms = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(Room(x=x, y=y))
            self.rooms.append(row)

        # Carve a path from entrance to stairs
        self.rooms[0][0].room_type = ENTRANCE
        self.rooms[0][0].explored = True
        self.player_x = 0
        self.player_y = 0

        # Place stairs
        stair_x = rng.randint(self.width - 2, self.width - 1)
        stair_y = rng.randint(self.height - 2, self.height - 1)
        self.rooms[stair_y][stair_x].room_type = STAIRS

        # Create walls (~20% of remaining cells)
        available = [
            (x, y) for y in range(self.height) for x in range(self.width)
            if (x, y) not in ((0, 0), (stair_x, stair_y))
        ]
        rng.shuffle(available)

        num_walls = int(len(available) * 0.2)
        wall_candidates = available[:num_walls]
        remaining = available[num_walls:]

        for wx, wy in wall_candidates:
            self.rooms[wy][wx].room_type = WALL

        # Verify path exists, remove walls if needed
        if not self._path_exists(0, 0, stair_x, stair_y):
            for wx, wy in wall_candidates:
                self.rooms[wy][wx].room_type = EMPTY
                remaining.append((wx, wy))
                if self._path_exists(0, 0, stair_x, stair_y):
                    break

        # Place content in remaining cells
        rng.shuffle(remaining)
        open_cells = [
            (x, y) for x, y in remaining
            if self.rooms[y][x].room_type == EMPTY
        ]

        # ── Boss (near stairs) ──────────────────────────────
        boss_placed = False
        for bx, by in [(stair_x - 1, stair_y), (stair_x, stair_y - 1)]:
            if 0 <= bx < self.width and 0 <= by < self.height:
                room = self.rooms[by][bx]
                if room.room_type == EMPTY:
                    room.room_type = BOSS
                    boss = boss_for_floor(self.number, biome)
                    room.enemy = dict(boss)
                    room.description = f"The air crackles. {boss['name']} blocks your path!"
                    boss_placed = True
                    if (bx, by) in open_cells:
                        open_cells.remove((bx, by))
                    break

        if not boss_placed and open_cells:
            bx, by = open_cells.pop(0)
            room = self.rooms[by][bx]
            room.room_type = BOSS
            boss = boss_for_floor(self.number, biome)
            room.enemy = dict(boss)
            room.description = f"The air crackles. {boss['name']} blocks your path!"

        # ── Enemies ─────────────────────────────────────────
        enemies = enemies_for_floor(self.number, biome)
        modifier_effects = (floor_modifier or {}).get("effects", {})
        enemy_mult = modifier_effects.get("enemy_count_mult", 1.0)
        base_enemies = rng.randint(3, 5)
        num_enemies = min(int(base_enemies * enemy_mult), len(open_cells))

        for i in range(num_enemies):
            if not open_cells:
                break
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            room.room_type = ENEMY
            enemy = rng.choice(enemies)
            room.enemy = dict(enemy)
            room.description = f"{enemy['name']} appears! {enemy['description']}"

        # ── Treasures ───────────────────────────────────────
        extra_treasure = int(modifier_effects.get("extra_treasure", 0))
        num_treasure = min(rng.randint(1, 2) + extra_treasure, len(open_cells))
        for i in range(num_treasure):
            if not open_cells:
                break
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            room.room_type = TREASURE
            room.description = rng.choice(room_descs.get(TREASURE, ROOM_DESCRIPTIONS[TREASURE]))

        # ── Rest point (skip if Cursed modifier) ────────────
        no_rest = modifier_effects.get("no_rest", False)
        if not no_rest and open_cells:
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            room.room_type = REST
            room.description = rng.choice(room_descs.get(REST, ROOM_DESCRIPTIONS[REST]))

        # ── Traps ───────────────────────────────────────────
        num_traps = min(rng.randint(1, 2), len(open_cells))
        for i in range(num_traps):
            if not open_cells:
                break
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            room.room_type = TRAP
            if biome_traps:
                trap = rng.choice(biome_traps)
                room.trap = dict(trap)
                room.description = trap.get("description", rng.choice(ROOM_DESCRIPTIONS[TRAP]))
            else:
                room.description = rng.choice(room_descs.get(TRAP, ROOM_DESCRIPTIONS[TRAP]))

        # ── Shop (every 3-4 floors) ────────────────────────
        if self.number % 3 == 0 and open_cells:
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            room.room_type = SHOP
            room.description = rng.choice(room_descs.get(SHOP, ROOM_DESCRIPTIONS[SHOP]))

        # ── Extraction (every 5 floors, near stairs) ────────
        if self.number % 5 == 0 and open_cells:
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            room.room_type = EXTRACTION
            room.description = rng.choice(room_descs.get(EXTRACTION, ROOM_DESCRIPTIONS[EXTRACTION]))

        # ── Cursed chest (15% chance, replaces a cell) ──────
        if rng.random() < 0.15 and open_cells:
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            room.room_type = CURSED_CHEST
            room.description = rng.choice(room_descs.get(CURSED_CHEST, ROOM_DESCRIPTIONS[CURSED_CHEST]))

        # ── Fork room (random, not too frequent) ────────────
        if rng.random() < 0.25 and open_cells:
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            room.room_type = FORK
            room.description = rng.choice(room_descs.get(FORK, ROOM_DESCRIPTIONS[FORK]))
            # Pick two random options
            opts = rng.sample(FORK_OPTIONS, min(2, len(FORK_OPTIONS)))
            room.fork_options = [(o[0], o[1]) for o in opts]

        # ── Companion stat influences ───────────────────────
        wisdom = stats.get("wisdom", 0)
        chaos_stat = stats.get("chaos", 0)

        # High WISDOM: reveal 1-2 extra rooms
        if wisdom >= 80:
            unexplored = [
                (x, y) for y in range(self.height) for x in range(self.width)
                if not self.rooms[y][x].explored and self.rooms[y][x].room_type != WALL
            ]
            reveal_count = min(rng.randint(1, 2), len(unexplored))
            for rx, ry in rng.sample(unexplored, reveal_count) if unexplored else []:
                self.rooms[ry][rx].explored = True

        # High CHAOS: 20% chance for weird encounter (bonus treasure or extra enemy)
        if chaos_stat >= 80 and rng.random() < 0.2 and open_cells:
            x, y = open_cells.pop(0)
            room = self.rooms[y][x]
            if rng.random() < 0.5:
                room.room_type = TREASURE
                room.description = "A chaotic rift reveals unexpected loot!"
            else:
                room.room_type = ENEMY
                enemy = rng.choice(enemies) if enemies else None
                if enemy:
                    room.enemy = dict(enemy)
                    room.description = f"A chaos rift spawns {enemy['name']}!"

        # ── Boss clues on boss floors ───────────────────────
        if biome_clues:
            clue_rooms = [
                (x, y) for y in range(self.height) for x in range(self.width)
                if self.rooms[y][x].room_type == EMPTY and not self.rooms[y][x].description.startswith("A ")
            ]
            num_clues = min(rng.randint(1, 2), len(clue_rooms), len(biome_clues))
            for cx, cy in rng.sample(clue_rooms, num_clues) if clue_rooms else []:
                self.rooms[cy][cx].description = rng.choice(biome_clues)

        # Fill remaining with descriptions
        for y in range(self.height):
            for x in range(self.width):
                room = self.rooms[y][x]
                if room.room_type == EMPTY and not room.description:
                    room.description = rng.choice(room_descs.get(EMPTY, ROOM_DESCRIPTIONS[EMPTY]))

    def _path_exists(self, sx: int, sy: int, ex: int, ey: int) -> bool:
        """BFS to check if a path exists between two points."""
        visited = set()
        queue = deque([(sx, sy)])
        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == (ex, ey):
                return True
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.rooms[ny][nx].room_type != WALL:
                        queue.append((nx, ny))
        return False

    def get_room(self, x: int, y: int) -> Room | None:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.rooms[y][x]
        return None

    def current_room(self) -> Room:
        return self.rooms[self.player_y][self.player_x]

    def can_move(self, dx: int, dy: int) -> bool:
        nx, ny = self.player_x + dx, self.player_y + dy
        if not (0 <= nx < self.width and 0 <= ny < self.height):
            return False
        return self.rooms[ny][nx].room_type != WALL

    def move_player(self, dx: int, dy: int) -> Room | None:
        if not self.can_move(dx, dy):
            return None
        self.player_x += dx
        self.player_y += dy
        room = self.current_room()
        room.explored = True
        # Reveal adjacent rooms (Fog modifier: no reveal)
        for adx, ady in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            adj = self.get_room(self.player_x + adx, self.player_y + ady)
            if adj and adj.room_type != WALL:
                adj.explored = True
        return room

    def move_player_fog(self, dx: int, dy: int) -> Room | None:
        """Move with fog modifier — only reveal current room, not adjacent."""
        if not self.can_move(dx, dy):
            return None
        self.player_x += dx
        self.player_y += dy
        room = self.current_room()
        room.explored = True
        return room

    def render_map(self) -> str:
        """Render the floor as ASCII art with large readable cells."""
        lines = []
        cw = 7  # cell inner width (chars between borders)
        sep = "─" * cw

        # Top border
        lines.append("┌" + (sep + "┬") * (self.width - 1) + sep + "┐")

        for y in range(self.height):
            # Content row
            row = "│"
            for x in range(self.width):
                room = self.rooms[y][x]
                pad = cw - 1  # chars around the symbol
                left = pad // 2
                right = pad - left
                sp_l = " " * left
                sp_r = " " * right
                if x == self.player_x and y == self.player_y:
                    cell = f"{sp_l}[bold #9ECE6A]@[/]{sp_r}"
                elif not room.explored:
                    cell = f"{sp_l}[dim]░[/]{sp_r}"
                elif room.room_type == WALL:
                    cell = f"{sp_l}[dim]#[/]{sp_r}"
                elif room.cleared or room.room_type in (EMPTY, ENTRANCE):
                    cell = f"{sp_l}[dim]·[/]{sp_r}"
                elif room.room_type == ENEMY:
                    cell = f"{sp_l}[bold #F7768E]![/]{sp_r}"
                elif room.room_type == BOSS:
                    cell = f"{sp_l}[bold #F7768E]B[/]{sp_r}"
                elif room.room_type == TREASURE:
                    cell = f"{sp_l}[bold #E0AF68]?[/]{sp_r}"
                elif room.room_type == REST:
                    cell = f"{sp_l}[bold #7AA2F7]+[/]{sp_r}"
                elif room.room_type == TRAP:
                    cell = f"{sp_l}[bold #BB9AF7]^[/]{sp_r}"
                elif room.room_type == STAIRS:
                    cell = f"{sp_l}[bold #BB9AF7]>[/]{sp_r}"
                elif room.room_type == SHOP:
                    cell = f"{sp_l}[bold #E0AF68]$[/]{sp_r}"
                elif room.room_type == FORK:
                    cell = f"{sp_l}[bold #7DCFFF]Y[/]{sp_r}"
                elif room.room_type == EXTRACTION:
                    cell = f"{sp_l}[bold #9ECE6A]E[/]{sp_r}"
                elif room.room_type == CURSED_CHEST:
                    cell = f"{sp_l}[bold #F7768E]C[/]{sp_r}"
                else:
                    cell = " " * cw
                row += cell + "│"
            lines.append(row)

            # Row separator
            if y < self.height - 1:
                lines.append("├" + (sep + "┼") * (self.width - 1) + sep + "┤")

        # Bottom border
        lines.append("└" + (sep + "┴") * (self.width - 1) + sep + "┘")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "number": self.number,
            "width": self.width,
            "height": self.height,
            "rooms": [[r.as_dict() for r in row] for row in self.rooms],
            "player_x": self.player_x,
            "player_y": self.player_y,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Floor:
        f = cls(number=data["number"], width=data["width"], height=data["height"])
        f.rooms = [[Room.from_dict(r) for r in row] for row in data["rooms"]]
        f.player_x = data["player_x"]
        f.player_y = data["player_y"]
        return f


def _desc_key_to_symbol(key: str) -> str | None:
    """Convert biome JSON description keys to room type symbols."""
    mapping = {
        "empty": EMPTY, "trap": TRAP, "rest": REST, "treasure": TREASURE,
        "shop": SHOP, "fork": FORK, "extraction": EXTRACTION,
        "cursed_chest": CURSED_CHEST,
    }
    return mapping.get(key)
