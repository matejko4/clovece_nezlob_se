from __future__ import annotations

import random
import time
from typing import Callable

import pygame


class Dice:
    """Dice handling and roll animation."""

    def roll(self) -> int:
        """Return random integer from 1 to 6."""
        return random.randint(1, 6)

    def animate_roll(
        self,
        surface: pygame.Surface,
        callback: Callable[[int], None],
        rect: pygame.Rect | None = None,
        face_color: tuple[int, int, int] | None = None,
    ) -> None:
        """Play a short dice animation and invoke callback with final value."""
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("arial", 44, bold=True)
        end_time = time.time() + 0.45
        value = 1
        panel = rect or pygame.Rect(760, 480, 120, 120)
        update_rect = panel.inflate(20, 20)
        tint = face_color or (245, 245, 245)

        while time.time() < end_time:
            value = self.roll()
            draw_color = (
                min(255, tint[0] + 30),
                min(255, tint[1] + 30),
                min(255, tint[2] + 30),
            )
            pygame.draw.rect(surface, draw_color, panel, border_radius=12)
            pygame.draw.rect(surface, (50, 50, 50), panel, width=3, border_radius=12)
            text = font.render(str(value), True, (20, 20, 20))
            surface.blit(text, text.get_rect(center=panel.center))
            pygame.display.update(update_rect)
            clock.tick(15)

        callback(value)
