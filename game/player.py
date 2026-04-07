from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from game.piece import Piece

if TYPE_CHECKING:
    from game.board import Board


@dataclass
class Player:
    """Represents a Ludo player and their pawns."""

    color: str
    name: str
    is_ai: bool = False
    score: int = 0
    pieces: list[Piece] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize four pieces for this player if not supplied."""
        if not self.pieces:
            self.pieces = [Piece(owner=self, piece_id=index) for index in range(4)]

    def all_pieces_home(self) -> bool:
        """Return True when all pieces are still in home."""
        return all(piece.is_at_home() for piece in self.pieces)

    def has_movable_piece(self, dice_value: int) -> bool:
        """Return True if at least one pawn can move for this dice value."""
        for piece in self.pieces:
            if piece.finished:
                continue
            if piece.is_at_home() and dice_value == 6:
                return True
            if not piece.is_at_home() and piece.progress + dice_value <= 43:
                return True
        return False

    def ai_choose_piece(self, dice_value: int, board: Board) -> Piece | None:
        """Simple AI: prefer capture first, then maximize progress."""
        candidates: list[tuple[int, int, Piece]] = []
        for piece in self.pieces:
            if not board.is_valid_move(piece, dice_value):
                continue
            preview = board.preview_move(piece, dice_value)
            capture_score = 1 if preview["captures"] > 0 else 0
            progress_score = preview["target_progress"]
            candidates.append((capture_score, progress_score, piece))

        if not candidates:
            return None

        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return candidates[0][2]
