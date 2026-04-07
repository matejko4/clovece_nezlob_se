from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.piece import Piece
    from game.player import Player


class Board:
    """Represents board state and movement rules."""

    NUM_CELLS = 40
    HOME_CELLS = 4
    START_POSITIONS = {"red": 0, "blue": 10, "green": 20, "yellow": 30}

    def __init__(self, players: list[Player] | None = None, safe_cells: list[int] | None = None) -> None:
        self.players: list[Player] = players or []
        self.safe_cells: set[int] = set(safe_cells or [0, 8, 13, 18, 21, 26, 31, 34, 39])
        self.safe_cells.update(self.START_POSITIONS.values())

    def set_players(self, players: list[Player]) -> None:
        """Attach players to board for occupancy checks."""
        self.players = players

    def is_safe_cell(self, position: int) -> bool:
        """Return True if a main-track cell is safe."""
        return position in self.safe_cells

    def get_cell_occupants(self, position: int) -> list[Piece]:
        """Return all pieces on a specific main-track cell."""
        if position < 0 or position >= self.NUM_CELLS:
            return []
        occupants: list[Piece] = []
        for player in self.players:
            for piece in player.pieces:
                if piece.position == position and not piece.finished:
                    occupants.append(piece)
        return occupants

    def preview_move(self, piece: Piece, steps: int) -> dict[str, int | bool]:
        """Preview move result without mutating state."""
        if piece.finished:
            return {"valid": False, "target_progress": piece.progress, "target_position": piece.position, "captures": 0}

        if piece.is_at_home():
            if steps != 6:
                return {"valid": False, "target_progress": -1, "target_position": -1, "captures": 0}
            target_progress = 0
        else:
            raw_target_progress = piece.progress + steps

            # New goal behavior: when crossing into goal, place piece into first free goal slot.
            if piece.progress < 40 and raw_target_progress >= 40:
                free_goal_slot = self._get_next_free_goal_slot(piece.owner)
                if free_goal_slot is None:
                    return {
                        "valid": False,
                        "target_progress": piece.progress,
                        "target_position": piece.position,
                        "captures": 0,
                    }
                target_progress = 40 + free_goal_slot
            else:
                target_progress = raw_target_progress
                if target_progress > 43:
                    return {
                        "valid": False,
                        "target_progress": piece.progress,
                        "target_position": piece.position,
                        "captures": 0,
                    }

        target_position = self._position_from_progress(piece.owner.color, target_progress)

        for other in piece.owner.pieces:
            if other is piece:
                continue
            if other.position == target_position:
                return {
                    "valid": False,
                    "target_progress": piece.progress,
                    "target_position": piece.position,
                    "captures": 0,
                }

        captures = 0
        if target_position < self.NUM_CELLS and not self.is_safe_cell(target_position):
            captures = len(
                [
                    other
                    for other in self.get_cell_occupants(target_position)
                    if other.owner.color != piece.owner.color
                ]
            )

        return {
            "valid": True,
            "target_progress": target_progress,
            "target_position": target_position,
            "captures": captures,
        }

    def is_valid_move(self, piece: Piece, steps: int) -> bool:
        """Validate if a piece can move by a number of steps."""
        return bool(self.preview_move(piece, steps)["valid"])

    def move_piece(self, piece: Piece, steps: int) -> str:
        """Move a piece and return movement result state."""
        preview = self.preview_move(piece, steps)
        if not preview["valid"]:
            return "blocked"

        piece.progress = int(preview["target_progress"])
        piece.position = int(preview["target_position"])

        captured_any = False
        if piece.position < self.NUM_CELLS and not self.is_safe_cell(piece.position):
            for occupant in self.get_cell_occupants(piece.position):
                if occupant.owner.color == piece.owner.color:
                    continue
                occupant.position = -1
                occupant.progress = -1
                occupant.finished = False
                captured_any = True

        if piece.position >= self.NUM_CELLS:
            piece.finished = True
            return "finished"

        if captured_any:
            return "captured"
        return "moved"

    def _position_from_progress(self, color: str, progress: int) -> int:
        """Map player-relative progress to global board position."""
        if progress <= 39:
            return (self.START_POSITIONS[color] + progress) % self.NUM_CELLS
        return progress

    def _get_next_free_goal_slot(self, owner: Player) -> int | None:
        """Return first free goal slot index (0..3) for owner, else None."""
        occupied_slots = {
            piece.position - self.NUM_CELLS
            for piece in owner.pieces
            if piece.position >= self.NUM_CELLS
        }

        for slot in range(self.HOME_CELLS):
            if slot not in occupied_slots:
                return slot
        return None
