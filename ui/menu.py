from __future__ import annotations

import sys

import pygame


class Menu:
    """Main menu and game result screens."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title_font = pygame.font.SysFont("arial", 48, bold=True)
        self.text_font = pygame.font.SysFont("arial", 28)

    def _draw_gradient_background(
        self,
        top_color: tuple[int, int, int],
        bottom_color: tuple[int, int, int],
        accent_color: tuple[int, int, int],
    ) -> None:
        width, height = self.screen.get_size()
        for y in range(height):
            ratio = y / max(1, height - 1)
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (width, y))

        glow = pygame.Surface((420, 420), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*accent_color, 55), (210, 210), 180)
        pygame.draw.circle(glow, (*accent_color, 30), (210, 210), 120)
        self.screen.blit(glow, (-80, -60))
        self.screen.blit(glow, (width - 340, height - 320))

    def show_main_menu(self) -> dict:
        """Display menu and return selected configuration."""
        num_players = 2
        ai_count = 0
        time_limit = 30
        selected = 0
        editing_name_index: int | None = None
        editing_name_backup: str = ""
        human_names = ["Hráč 1", "Hráč 2", "Hráč 3", "Hráč 4"]

        clock = pygame.time.Clock()

        while True:
            human_count = max(0, num_players - ai_count)
            start_index = 3 + human_count
            total_options = start_index + 1
            selected = max(0, min(selected, total_options - 1))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.KEYDOWN:
                    if editing_name_index is not None:
                        if event.key == pygame.K_RETURN:
                            current = human_names[editing_name_index].strip()
                            if not current:
                                human_names[editing_name_index] = f"Hráč {editing_name_index + 1}"
                            editing_name_index = None
                        elif event.key == pygame.K_ESCAPE:
                            human_names[editing_name_index] = editing_name_backup
                            editing_name_index = None
                        elif event.key == pygame.K_BACKSPACE:
                            human_names[editing_name_index] = human_names[editing_name_index][:-1]
                        else:
                            if event.unicode.isprintable() and len(human_names[editing_name_index]) < 16:
                                human_names[editing_name_index] += event.unicode
                        continue

                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % total_options
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % total_options
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        delta = -1 if event.key == pygame.K_LEFT else 1
                        if selected == 0:
                            num_players = max(2, min(4, num_players + delta))
                            ai_count = min(ai_count, num_players)
                        elif selected == 1:
                            ai_count = max(0, min(num_players, ai_count + delta))
                        elif selected == 2:
                            time_limit = max(10, min(120, time_limit + delta * 5))
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and selected == start_index:
                        ai_players = list(range(num_players - ai_count, num_players))
                        player_names: list[str] = []
                        for index in range(num_players):
                            if index < human_count:
                                name = human_names[index].strip() or f"Hráč {index + 1}"
                                player_names.append(name)
                            else:
                                player_names.append("")
                        
                        player_names = self._ensure_unique_names(player_names)
                        return {
                            "num_players": num_players,
                            "ai_players": ai_players,
                            "time_limit": time_limit,
                            "player_names": player_names,
                        }
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and 3 <= selected < start_index:
                        editing_name_index = selected - 3
                        editing_name_backup = human_names[editing_name_index]
                        human_names[editing_name_index] = ""

            width, height = self.screen.get_size()
            center_x = width // 2
            panel = pygame.Rect(0, 0, min(760, width - 80), min(560, height - 80))
            panel.center = (center_x, height // 2)

            self._draw_gradient_background((255, 189, 123), (255, 110, 135), (255, 246, 143))
            pygame.draw.rect(self.screen, (255, 248, 236), panel, border_radius=24)
            pygame.draw.rect(self.screen, (110, 35, 50), panel, width=4, border_radius=24)

            title = self.title_font.render("Člověče, nezlob se", True, (58, 28, 38))
            self.screen.blit(title, title.get_rect(center=(center_x, panel.top + 74)))

            lines = [
                f"Počet hráčů: {num_players}",
                f"Počet AI: {ai_count}",
                f"Čas tahu (s): {time_limit}",
            ]
            for idx in range(human_count):
                suffix = "  <piš jméno>" if editing_name_index == idx else ""
                lines.append(f"Jméno hráče {idx + 1}: {human_names[idx]}{suffix}")
            lines.append("Spustit hru")

            y = panel.top + 170
            for index, line in enumerate(lines):
                color = (35, 102, 190) if index == selected else (55, 45, 45)
                text = self.text_font.render(line, True, color)
                self.screen.blit(text, text.get_rect(center=(center_x, y)))
                y += 62

            hint_text = "ŠIPKY = výběr, ENTER = potvrdit/upravit"
            if editing_name_index is not None:
                hint_text = "Psaní jména, BACKSPACE = mazat, ENTER = uložit"
            hint = self.text_font.render(hint_text, True, (85, 70, 70))
            self.screen.blit(hint, hint.get_rect(center=(center_x, panel.bottom - 40)))

            pygame.display.flip()
            clock.tick(60)

    def show_game_over(self, leaderboard: list[dict]) -> None:
        """Show final leaderboard and wait for keypress."""
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    return

            width, height = self.screen.get_size()
            center_x = width // 2
            panel = pygame.Rect(0, 0, min(860, width - 80), min(620, height - 80))
            panel.center = (center_x, height // 2)

            self._draw_gradient_background((119, 187, 255), (51, 88, 168), (255, 255, 255))
            pygame.draw.rect(self.screen, (244, 249, 255), panel, border_radius=24)
            pygame.draw.rect(self.screen, (39, 72, 130), panel, width=4, border_radius=24)

            title = self.title_font.render("Konec hry", True, (28, 56, 110))
            self.screen.blit(title, title.get_rect(center=(center_x, panel.top + 60)))

            y = panel.top + 130
            for rank, row in enumerate(leaderboard, start=1):
                line = (
                    f"{rank}. {row['name']} | hra: {row['score']} b "
                    f"| celkem: {row['total_score']} b | výhry: {row['total_wins']}"
                )
                text = self.text_font.render(line, True, (30, 30, 30))
                self.screen.blit(text, text.get_rect(center=(center_x, y)))
                y += 56

            hint = self.text_font.render("Stiskni libovolnou klávesu", True, (60, 60, 60))
            self.screen.blit(hint, hint.get_rect(center=(center_x, panel.bottom - 34)))
            pygame.display.flip()
            clock.tick(60)

    def show_pause_menu(self) -> str:
        """Display pause options and return selected action."""
        clock = pygame.time.Clock()
        options = ["resume", "restart", "quit"]
        selected = 0

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return options[selected]
                    elif event.key == pygame.K_ESCAPE:
                        return "resume"

            width, height = self.screen.get_size()
            center_x = width // 2
            panel = pygame.Rect(0, 0, min(640, width - 80), min(440, height - 80))
            panel.center = (center_x, height // 2)

            self._draw_gradient_background((36, 25, 70), (96, 44, 136), (177, 142, 255))
            pygame.draw.rect(self.screen, (248, 240, 255), panel, border_radius=22)
            pygame.draw.rect(self.screen, (83, 48, 120), panel, width=4, border_radius=22)
            self.screen.blit(self.title_font.render("Pauza", True, (71, 32, 105)), (panel.left + 26, panel.top + 28))

            y = panel.top + 130
            labels = {"resume": "Pokračovat", "restart": "Restart", "quit": "Konec"}
            for index, key in enumerate(options):
                color = (220, 112, 26) if index == selected else (80, 54, 94)
                text = self.text_font.render(labels[key], True, color)
                self.screen.blit(text, text.get_rect(center=(center_x, y)))
                y += 70

            pygame.display.flip()
            clock.tick(60)

    def _ensure_unique_names(self, player_names: list[str]) -> list[str]:
        """Ensure all human player names are unique by appending numbers to duplicates."""
        result = []
        seen_names = {}
        
        for index, name in enumerate(player_names):
            if not name:
                result.append(name)
                continue
            
            if name not in seen_names:
                seen_names[name] = 0
                result.append(name)
            else:
                seen_names[name] += 1
                new_name = f"{name} {seen_names[name]}"
                while new_name in seen_names:
                    seen_names[name] += 1
                    new_name = f"{name} {seen_names[name]}"
                seen_names[new_name] = 0
                result.append(new_name)
        
        return result
