from __future__ import annotations

import threading
import time
from typing import Callable


class TimerManager:
    """Per-turn countdown timer."""

    def __init__(self, time_limit_seconds: int) -> None:
        self.time_limit_seconds = max(1, int(time_limit_seconds))
        self._start_time: float | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._on_timeout: Callable[[], None] | None = None
        self._expired = False
        self._lock = threading.Lock()

    def start(self, on_timeout_callback: Callable[[], None]) -> None:
        """Start countdown and call callback after timeout."""
        self.stop()
        with self._lock:
            self._on_timeout = on_timeout_callback
            self._start_time = time.time()
            self._expired = False
            self._stop_event.clear()
        self._thread = threading.Thread(target=self._watcher, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the running timer."""
        self._stop_event.set()
        with self._lock:
            self._start_time = None

    def reset(self) -> None:
        """Reset timer state without starting it."""
        self.stop()
        with self._lock:
            self._expired = False

    def get_remaining(self) -> float:
        """Return remaining seconds in active timer."""
        with self._lock:
            if self._start_time is None:
                return float(self.time_limit_seconds)
            elapsed = time.time() - self._start_time
        return max(0.0, self.time_limit_seconds - elapsed)

    def is_expired(self) -> bool:
        """Return True if timer has expired."""
        with self._lock:
            return self._expired

    def _watcher(self) -> None:
        """Background watcher loop used to trigger timeout callback."""
        while not self._stop_event.is_set():
            if self.get_remaining() <= 0:
                with self._lock:
                    self._expired = True
                callback = self._on_timeout
                if callback is not None:
                    callback()
                self._stop_event.set()
                return
            time.sleep(0.05)
