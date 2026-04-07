from __future__ import annotations

import pygame


class HUD:
    """Heads-up display with timer, active player and scores."""

    def __init__(self) -> None:
        self.panel = pygame.Rect(740, 20, 340, 700)
        self.title_font = pygame.font.SysFont("verdana", 28, bold=True)
        self.text_font = pygame.font.SysFont("verdana", 20)
        self.small_font = pygame.font.SysFont("verdana", 16)
        self.player_colors = {
            "red": (205, 60, 60),
            "blue": (65, 108, 210),
            "green": (50, 165, 92),
            "yellow": (230, 193, 58),
        }

    def set_panel_rect(self, panel_rect: pygame.Rect) -> None:
        """Update HUD layout rectangle from renderer scene layout."""
        self.panel = panel_rect.copy()

    def draw(self, surface, players, current_player, timer, scores, game_remaining_seconds: float) -> None:
        """Render game HUD information."""
        left = self.panel.left + 20
        right = self.panel.right - 20
        content_width = self.panel.width - 40

        shadow = self.panel.move(4, 4)
        pygame.draw.rect(surface, (0, 0, 0, 45), shadow, border_radius=14)
        pygame.draw.rect(surface, (248, 246, 241), self.panel, border_radius=14)
        pygame.draw.rect(surface, (50, 50, 50), self.panel, width=2, border_radius=14)

        y = self.panel.top + 20
        title = self.title_font.render("Stav hry", True, (30, 30, 30))
        surface.blit(title, (left, y))
        y += 48

        player_color = self.player_colors.get(current_player.color, (100, 100, 100))
        turn_box = pygame.Rect(left, y, content_width, 56)
        pygame.draw.rect(surface, (236, 235, 228), turn_box, border_radius=12)
        pygame.draw.rect(surface, player_color, turn_box, width=3, border_radius=12)
        pygame.draw.circle(surface, player_color, (turn_box.left + 24, turn_box.centery), 10)
        turn_label = self.small_font.render("NA TAHU", True, (60, 60, 60))
        turn_name = self.text_font.render(current_player.name, True, (20, 20, 20))
        surface.blit(turn_label, (turn_box.left + 42, turn_box.top + 7))
        surface.blit(turn_name, (turn_box.left + 42, turn_box.top + 26))
        y += 68

        game_ratio = max(0.0, min(1.0, game_remaining_seconds / 300.0))
        pygame.draw.rect(surface, (220, 220, 220), (left, y, content_width, 14), border_radius=7)
        pygame.draw.rect(surface, (88, 143, 207), (left, y, int(content_width * game_ratio), 14), border_radius=7)
        total_time_label = self.text_font.render(f"Konec hry za: {game_remaining_seconds:05.1f}s", True, (20, 20, 20))
        surface.blit(total_time_label, (left, y + 18))
        y += 56

        remaining = timer.get_remaining()
        ratio = remaining / float(timer.time_limit_seconds)
        ratio = max(0.0, min(1.0, ratio))
        pygame.draw.rect(surface, (220, 220, 220), (left, y, content_width, 18), border_radius=9)
        color = (72, 173, 101) if ratio > 0.35 else (212, 139, 56)
        if ratio < 0.15:
            color = (196, 70, 70)
        pygame.draw.rect(surface, color, (left, y, int(content_width * ratio), 18), border_radius=9)
        label = self.text_font.render(f"Čas: {remaining:04.1f}s", True, (20, 20, 20))
        surface.blit(label, (left, y + 24))
        y += 66

        surface.blit(self.title_font.render("Skóre", True, (30, 30, 30)), (left, y))
        y += 38

        for player in players:
            finished = sum(1 for piece in player.pieces if piece.finished)
            line = f"{player.name}: {player.score} b | cíl: {finished}/4"
            color_mark = (20, 20, 20)
            if player is current_player:
                color_mark = (12, 84, 145)
            line = self._fit_text(self.text_font, line, content_width - 10)
            text = self.text_font.render(line, True, color_mark)
            surface.blit(text, (left, y))
            y += 30

        y += 24
        surface.blit(self.title_font.render("Celkově", True, (30, 30, 30)), (left, y))
        y += 38
        for row in scores[:4]:
            line = f"{row['name']}: {row['total_score']} b | výhry: {row['total_wins']}"
            line = self._fit_text(self.text_font, line, content_width - 10)
            text = self.text_font.render(line, True, (20, 20, 20))
            surface.blit(text, (left, y))
            y += 28

        y += 16
        pygame.draw.line(surface, (200, 200, 200), (left, y), (right, y), 1)
        y += 14
        legend_title = self.small_font.render("Legenda", True, (40, 40, 40))
        surface.blit(legend_title, (left, y))
        y += 24

        star = self.text_font.render("*", True, (84, 74, 36))
        surface.blit(star, (left, y - 3))
        legend_text = self._fit_text(self.small_font, "Hvězdička = bezpečné pole (nelze sebrat)", content_width - 30)
        legend = self.small_font.render(legend_text, True, (45, 45, 45))
        surface.blit(legend, (left + 20, y))

    def _fit_text(self, font: pygame.font.Font, text: str, max_width: int) -> str:
        """Trim text with ellipsis so it always fits into panel width."""
        if font.size(text)[0] <= max_width:
            return text

        trimmed = text
        while trimmed and font.size(trimmed + "...")[0] > max_width:
            trimmed = trimmed[:-1]
        return trimmed + "..."
