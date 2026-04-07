from __future__ import annotations

import logging

from game.player import Player
from managers.data_manager import DataCorruptedError, DataManager
from managers.security_manager import SecurityManager


class ScoreManager:
    """Handles in-game points and persistent leaderboard."""

    POINTS_FINISH_PIECE = 10
    POINTS_CAPTURE = 5
    POINTS_WIN_BONUS = 30
    POINTS_QUIZ_CORRECT = 10
    PENALTY_TIMEOUT = -2
    PENALTY_QUIZ_WRONG = -5

    def __init__(
        self,
        data_manager: DataManager,
        security_manager: SecurityManager,
        score_file: str = "data/scores.json.enc",
        scoring_config: dict | None = None,
    ) -> None:
        self.data_manager = data_manager
        self.security_manager = security_manager
        self.score_file = score_file
        self.persistent_scores: dict = {"players": []}
        self.runtime_players: list[Player] = []

        if scoring_config:
            self.POINTS_FINISH_PIECE = int(scoring_config.get("finish_piece", self.POINTS_FINISH_PIECE))
            self.POINTS_CAPTURE = int(scoring_config.get("capture", self.POINTS_CAPTURE))
            self.POINTS_WIN_BONUS = int(scoring_config.get("win_bonus", self.POINTS_WIN_BONUS))
            self.PENALTY_TIMEOUT = int(scoring_config.get("timeout_penalty", self.PENALTY_TIMEOUT))

        self.load_scores()

    def register_players(self, players: list[Player]) -> None:
        """Attach runtime players and ensure persistent entries exist."""
        self.runtime_players = players
        for player in players:
            if self._find_or_create_entry(player.name) is None:
                logging.warning("Failed to create score entry for %s", player.name)

    def add_points(self, player: Player, reason: str) -> None:
        """Apply positive points to player and persistent score."""
        amount = {
            "finish_piece": self.POINTS_FINISH_PIECE,
            "capture": self.POINTS_CAPTURE,
            "win_bonus": self.POINTS_WIN_BONUS,
            "quiz_correct": self.POINTS_QUIZ_CORRECT,
        }.get(reason, 0)
        player.score += amount
        entry = self._find_or_create_entry(player.name)
        entry["total_score"] += amount

    def apply_penalty(self, player: Player, reason: str) -> None:
        """Apply penalty points to player and persistent score."""
        amount = {
            "timeout": self.PENALTY_TIMEOUT,
            "quiz_wrong": self.PENALTY_QUIZ_WRONG,
        }.get(reason, 0)
        player.score += amount
        entry = self._find_or_create_entry(player.name)
        entry["total_score"] += amount

    def record_win(self, player: Player) -> None:
        """Record game win in persistent storage."""
        entry = self._find_or_create_entry(player.name)
        entry["total_wins"] += 1

    def get_leaderboard(self) -> list[dict]:
        """Return sorted leaderboard for runtime players."""
        rows: list[dict] = []
        for player in self.runtime_players:
            entry = self._find_or_create_entry(player.name)
            rows.append(
                {
                    "name": player.name,
                    "color": player.color,
                    "score": player.score,
                    "total_score": entry["total_score"],
                    "total_wins": entry["total_wins"],
                    "finished_pieces": sum(1 for piece in player.pieces if piece.finished),
                }
            )
        rows.sort(key=lambda row: (row["score"], row["total_score"]), reverse=True)
        return rows

    def save_scores(self) -> None:
        """Persist encrypted scoreboard."""
        self.data_manager.save_encrypted(self.score_file, self.persistent_scores, self.security_manager)

    def load_scores(self) -> None:
        """Load encrypted scoreboard and recover on corruption."""
        try:
            loaded = self.data_manager.load_encrypted(self.score_file, self.security_manager)
            if isinstance(loaded, dict) and "players" in loaded and isinstance(loaded["players"], list):
                self.persistent_scores = loaded
            else:
                self.persistent_scores = {"players": []}
        except DataCorruptedError:
            logging.warning("Encrypted score file is corrupted, starting with empty scores.")
            self.persistent_scores = {"players": []}

    def _find_or_create_entry(self, player_name: str) -> dict:
        """Find existing persistent player stats or create new record."""
        for entry in self.persistent_scores["players"]:
            if entry["name"] == player_name:
                return entry
        entry = {"name": player_name, "total_wins": 0, "total_score": 0}
        self.persistent_scores["players"].append(entry)
        return entry
