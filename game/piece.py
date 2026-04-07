from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.player import Player


@dataclass
class Piece:
    """Represents a single pawn on the board."""

    owner: Player
    piece_id: int
    position: int = -1
    finished: bool = False
    progress: int = -1

    def is_at_home(self) -> bool:
        """Return True if the pawn is in home."""
        return self.position == -1 and not self.finished

    def is_finished(self) -> bool:
        """Return True if the pawn has reached final goal."""
        return self.finished
