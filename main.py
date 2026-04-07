from __future__ import annotations

import sys

import pygame

from game.game import Game
from ui.menu import Menu


def main() -> None:
    """Application entry point."""
    pygame.init()
    display_info = pygame.display.Info()
    screen = pygame.display.set_mode((display_info.current_w, display_info.current_h), pygame.FULLSCREEN)
    pygame.display.set_caption("Člověče, nezlob se")

    menu = Menu(screen)

    while True:
        config = menu.show_main_menu()

        game = Game(
            num_players=config["num_players"],
            ai_players=config["ai_players"],
            time_limit=config["time_limit"],
            player_names=config.get("player_names"),
        )
        restart_to_menu = game.start()
        if not restart_to_menu:
            break

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
