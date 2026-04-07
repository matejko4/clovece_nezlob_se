from __future__ import annotations

import pygame


class Dialogs:
    """Simple utility dialogs and transient notifications."""

    def __init__(self) -> None:
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.quiz_title_font = pygame.font.SysFont("arial", 30, bold=True)
        self.quiz_font = pygame.font.SysFont("arial", 22)

    def draw_notification(self, surface: pygame.Surface, message: str) -> None:
        """Draw temporary message overlay."""
        width, height = surface.get_size()
        box = pygame.Rect(0, 0, 560, 44)
        box.midbottom = (width // 2, height - 22)
        pygame.draw.rect(surface, (25, 25, 25), box, border_radius=10)
        pygame.draw.rect(surface, (245, 245, 245), box, width=2, border_radius=10)
        text = self.font.render(message, True, (245, 245, 245))
        surface.blit(text, text.get_rect(center=box.center))

    def draw_error_feedback(self, surface: pygame.Surface) -> None:
        """Draw quick visual feedback for invalid click/action."""
        width, _ = surface.get_size()
        box = pygame.Rect(0, 0, 520, 36)
        box.midtop = (width // 2, 20)
        pygame.draw.rect(surface, (188, 44, 44), box, border_radius=8)
        text = self.font.render("Neplatný tah", True, (255, 255, 255))
        surface.blit(text, text.get_rect(center=box.center))

    def draw_quiz_question(
        self,
        surface: pygame.Surface,
        player_name: str,
        question: str,
        options: list[str],
    ) -> list[pygame.Rect]:
        """Draw modal quiz question and return option rects for click handling."""
        width, height = surface.get_size()

        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(0, 0, 760, 360)
        panel.center = (width // 2, height // 2)
        pygame.draw.rect(surface, (250, 248, 240), panel, border_radius=18)
        pygame.draw.rect(surface, (35, 35, 35), panel, width=3, border_radius=18)

        title = self.quiz_title_font.render(f"Otázka pro {player_name}", True, (25, 25, 25))
        surface.blit(title, title.get_rect(midtop=(panel.centerx, panel.top + 18)))

        q_text = self.quiz_font.render(question, True, (35, 35, 35))
        surface.blit(q_text, q_text.get_rect(midtop=(panel.centerx, panel.top + 72)))

        hint = self.quiz_font.render("Vyber odpověď 1-3", True, (70, 70, 70))
        surface.blit(hint, hint.get_rect(midtop=(panel.centerx, panel.top + 106)))

        option_rects: list[pygame.Rect] = []
        y = panel.top + 150
        for index, option in enumerate(options[:3], start=1):
            rect = pygame.Rect(panel.left + 70, y, panel.width - 140, 54)
            pygame.draw.rect(surface, (237, 233, 220), rect, border_radius=10)
            pygame.draw.rect(surface, (80, 80, 80), rect, width=2, border_radius=10)
            text = self.quiz_font.render(f"{index}. {option}", True, (30, 30, 30))
            surface.blit(text, text.get_rect(midleft=(rect.left + 16, rect.centery)))
            option_rects.append(rect)
            y += 64

        return option_rects

    def draw_quiz_result(self, surface: pygame.Surface, player_name: str, is_correct: bool) -> None:
        """Draw result panel after answering quiz question."""
        width, height = surface.get_size()

        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(0, 0, 560, 220)
        panel.center = (width // 2, height // 2)

        color = (48, 168, 95) if is_correct else (210, 70, 70)
        text = "Správně!" if is_correct else "Špatná odpověď"
        detail = "+10 bodů a můžeš pokračovat" if is_correct else "-5 bodů a tah je přeskočen"

        pygame.draw.rect(surface, (248, 246, 238), panel, border_radius=18)
        pygame.draw.rect(surface, color, panel, width=5, border_radius=18)

        title = self.quiz_title_font.render(text, True, color)
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 64)))

        info = self.quiz_font.render(player_name, True, (28, 28, 28))
        surface.blit(info, info.get_rect(center=(panel.centerx, panel.top + 112)))

        extra = self.quiz_font.render(detail, True, (55, 55, 55))
        surface.blit(extra, extra.get_rect(center=(panel.centerx, panel.top + 154)))
