from __future__ import annotations

from textual.widgets import Static

from ..constants import ADULT_FRAMES, JUVENILE_FRAMES, SNAIL_FRAMES


def frames_for(stage: str, specialization: str | None = None, species: str = "snail", eyes: str = "·") -> list[str]:
    """Get animation frames for a species/stage/specialization."""
    try:
        from ..species_art import get_frames
        return get_frames(species, stage, specialization, eyes)
    except (ImportError, KeyError):
        pass
    # Fallback to original snail-only constants
    if stage == "adult" and specialization and specialization in ADULT_FRAMES:
        return ADULT_FRAMES[specialization]
    if stage == "juvenile":
        return JUVENILE_FRAMES
    return SNAIL_FRAMES


class CompanionArt(Static):
    """Animated ASCII art that alternates between frames."""

    def __init__(
        self,
        stage: str = "hatchling",
        specialization: str | None = None,
        species: str = "snail",
        eyes: str = "·",
        **kwargs,
    ) -> None:
        self._frame_idx = 0
        self._species = species
        self._eyes = eyes
        self._frames = frames_for(stage, specialization, species, eyes)
        super().__init__(self._frames[0], **kwargs)

    def set_stage(self, stage: str, specialization: str | None = None, species: str | None = None, eyes: str | None = None) -> None:
        if species is not None:
            self._species = species
        if eyes is not None:
            self._eyes = eyes
        self._frames = frames_for(stage, specialization, self._species, self._eyes)
        self._frame_idx = 0
        self.update(self._frames[0])

    def next_frame(self) -> None:
        self._frame_idx = (self._frame_idx + 1) % len(self._frames)
        self.update(self._frames[self._frame_idx])


# Backward compatibility alias
SnailArt = CompanionArt
