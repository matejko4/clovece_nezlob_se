from __future__ import annotations

from game.player import Player
from managers.timer_manager import TimerManager


class RoundManager:
    """Controls turn order and timeout signaling."""

    def __init__(self, players: list[Player], timer: TimerManager) -> None:
        self.players = players
        self.timer = timer
        self.current_index = 0
        self.timed_out = False

    @property
    def current_player(self) -> Player:
        """Return player who is currently on turn."""
        return self.players[self.current_index]

    def start_turn(self, player: Player) -> None:
        """Start timer for active player turn."""
        self.timed_out = False
        self.timer.reset()
        self.timer.start(self.on_timeout)

    def end_turn(self) -> None:
        """Stop timer and move to next player."""
        self.timer.stop()
        self.current_index = (self.current_index + 1) % len(self.players)

    def on_timeout(self) -> None:
        """Callback used when active timer expires."""
        self.timed_out = True
