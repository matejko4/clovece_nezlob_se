from __future__ import annotations

import logging
import random
import sys
from typing import Sequence

import pygame

from game.board import Board
from game.dice import Dice
from game.player import Player
from game.round_manager import RoundManager
from managers.data_manager import DataManager
from managers.score_manager import ScoreManager
from managers.security_manager import SecurityManager
from managers.timer_manager import TimerManager
from ui.dialogs import Dialogs
from ui.hud import HUD
from ui.menu import Menu
from ui.renderer import Renderer


class Game:
    """Main game controller for desktop Ludo."""

    COLORS: Sequence[str] = ("red", "blue", "green", "yellow")
    GAME_DURATION_SECONDS = 300

    def __init__(
        self,
        num_players: int,
        ai_players: list[int],
        time_limit: int,
        player_names: list[str] | None = None,
    ) -> None:
        self.screen = pygame.display.get_surface()
        if self.screen is None:
            raise RuntimeError("Pygame display must be initialized before Game.")

        logging.basicConfig(level=logging.INFO)

        self.data_manager = DataManager()
        self.config = self.data_manager.load_config()

        self.num_players = max(2, min(int(num_players), int(self.config.get("max_players", 4))))
        self.ai_players = set(ai_players)
        self.time_limit = int(time_limit or self.config.get("time_limit_seconds", 30))
        self.player_names = list(player_names or [])

        self.players = self._build_players()
        self.board = Board(players=self.players, safe_cells=self.config.get("safe_cells", []))

        self.timer_manager = TimerManager(self.time_limit)
        self.round_manager = RoundManager(self.players, self.timer_manager)
        self.security_manager = SecurityManager()
        self.score_manager = ScoreManager(
            data_manager=self.data_manager,
            security_manager=self.security_manager,
            scoring_config=self.config.get("scoring", {}),
        )
        self.score_manager.register_players(self.players)

        self.renderer = Renderer(safe_cells=self.config.get("safe_cells", []))
        self.hud = HUD()
        self.dialogs = Dialogs()
        self.menu = Menu(self.screen)
        self.dice = Dice()
        self.player_colors = self.renderer.COLORS

        self.current_roll: int | None = None
        self.last_dice_value: int | None = None
        self.last_dice_owner_name: str | None = None
        self.last_dice_color: tuple[int, int, int] = (240, 240, 240)
        self.awaiting_selection = False
        self.valid_pieces: list = []
        self.running = True
        self.animating_roll = False
        self.pending_timeout_skip = False
        self.consecutive_sixes = 0

        self.notification = "Mezerník = hod kostkou"
        self.notification_until: int | None = None
        self.notification_sticky = True
        self.invalid_feedback_until = 0
        self.ai_next_action_at = pygame.time.get_ticks() + 450
        self.game_start_ticks = pygame.time.get_ticks()

        self.player_roll_counts: dict[str, int] = {player.name: 0 for player in self.players}
        self.quiz_active = False
        self.quiz_data: dict | None = None
        self.quiz_option_rects: list[pygame.Rect] = []
        self.quiz_pass_for: tuple[str, int] | None = None
        self.quiz_bank = self.data_manager.load_quiz_questions()
        self.quiz_feedback: dict | None = None
        self.return_to_main_menu = False

    def start(self) -> bool:
        """Start the main game loop and return True when user requested restart to main menu."""
        clock = pygame.time.Clock()
        self.game_start_ticks = pygame.time.get_ticks()
        self.round_manager.start_turn(self.round_manager.current_player)
        self._set_turn_instruction()

        while self.running:
            self._process_events()

            if self.round_manager.timed_out and not self.pending_timeout_skip:
                self.pending_timeout_skip = True

            if self.quiz_feedback is not None:
                self._update_quiz_feedback()

            if self._is_game_time_over() and self.check_win_condition() is None:
                self.end_game(by_timer=True)
                continue

            if self.pending_timeout_skip and not self.animating_roll:
                self._handle_timeout_skip()

            if self.round_manager.current_player.is_ai and not self.animating_roll:
                self._process_ai_turn()

            self._draw_frame()
            pygame.display.flip()
            clock.tick(60)

        self._safe_shutdown()
        return self.return_to_main_menu

    def next_turn(self) -> None:
        """Move to next player turn and reset turn state."""
        self.awaiting_selection = False
        self.valid_pieces.clear()
        self.current_roll = None
        self.consecutive_sixes = 0
        self.quiz_active = False
        self.quiz_data = None
        self.quiz_option_rects = []
        self.quiz_pass_for = None
        self.quiz_feedback = None

        self.round_manager.end_turn()
        self.round_manager.start_turn(self.round_manager.current_player)
        self.ai_next_action_at = pygame.time.get_ticks() + 500
        self._set_turn_instruction()

    def check_win_condition(self) -> Player | None:
        """Return winning player or None."""
        for player in self.players:
            if all(piece.finished for piece in player.pieces):
                return player
        return None

    def end_game(self, by_timer: bool = False) -> None:
        """Stop gameplay, save scores and display final ranking."""
        winner = self.check_win_condition()
        if by_timer:
            winner = self._pick_score_winner()
            if winner is not None:
                self.score_manager.record_win(winner)
        elif winner is not None:
            self.score_manager.add_points(winner, "win_bonus")
            self.score_manager.record_win(winner)

        self.score_manager.save_scores()
        leaderboard = self.score_manager.get_leaderboard()
        self.menu.show_game_over(leaderboard)
        self.running = False

    def _build_players(self) -> list[Player]:
        players: list[Player] = []
        for index, color in enumerate(self.COLORS[: self.num_players]):
            is_ai = index in self.ai_players
            custom_name = ""
            if index < len(self.player_names):
                custom_name = str(self.player_names[index]).strip()
            if is_ai:
                name = custom_name or f"AI {index + 1}"
            else:
                name = custom_name or f"Hráč {index + 1}"
            players.append(Player(color=color, name=name, is_ai=is_ai))
        return players

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    choice = self.menu.show_pause_menu()
                    if choice == "quit":
                        self.running = False
                    elif choice == "restart":
                        self._restart_game()
                    return

                if self.quiz_active:
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        quiz_choice = {
                            pygame.K_1: 0,
                            pygame.K_2: 1,
                            pygame.K_3: 2,
                        }[event.key]
                        self._handle_quiz_answer(quiz_choice)
                    continue

                if self.quiz_feedback is not None:
                    continue

                if self.round_manager.current_player.is_ai:
                    continue

                if event.key == pygame.K_SPACE and not self.awaiting_selection:
                    self._roll_dice()
                elif self.awaiting_selection and event.key in (
                    pygame.K_1,
                    pygame.K_2,
                    pygame.K_3,
                    pygame.K_4,
                ):
                    key_to_index = {
                        pygame.K_1: 0,
                        pygame.K_2: 1,
                        pygame.K_3: 2,
                        pygame.K_4: 3,
                    }
                    selected = key_to_index[event.key]
                    if 0 <= selected < len(self.round_manager.current_player.pieces):
                        piece = self.round_manager.current_player.pieces[selected]
                        self._try_move_piece(piece)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                try:
                    if self.quiz_active:
                        for index, rect in enumerate(self.quiz_option_rects):
                            if rect.collidepoint(event.pos):
                                self._handle_quiz_answer(index)
                                break
                        continue

                    if self.quiz_feedback is not None:
                        continue

                    if not self.awaiting_selection:
                        self.invalid_feedback_until = pygame.time.get_ticks() + 400
                        continue
                    piece = self.renderer.get_piece_at_pixel(event.pos)
                    if piece is None:
                        self.invalid_feedback_until = pygame.time.get_ticks() + 450
                        continue
                    self._try_move_piece(piece)
                except Exception:
                    logging.exception("Invalid mouse interaction was ignored.")

    def _roll_dice(self) -> None:
        if self.animating_roll:
            return
        if self.round_manager.timed_out:
            self.pending_timeout_skip = True
            return

        current_player = self.round_manager.current_player
        next_roll_number = self.player_roll_counts[current_player.name] + 1
        if next_roll_number % 5 == 0 and self.quiz_pass_for != (current_player.name, next_roll_number):
            self._start_quiz(current_player, next_roll_number)
            return

        self.renderer.update_layout(self.screen.get_size())
        self.animating_roll = True
        self.last_dice_owner_name = current_player.name
        self.last_dice_color = self.player_colors.get(current_player.color, (240, 240, 240))
        self.dice.animate_roll(
            self.screen,
            self._on_roll_result,
            rect=self.renderer.dice_rect,
            face_color=self.last_dice_color,
        )
        self.animating_roll = False
        self.quiz_pass_for = None

        if self.round_manager.timed_out:
            self.pending_timeout_skip = True
            return

        if current_player.is_ai and self.awaiting_selection:
            piece = current_player.ai_choose_piece(self.current_roll or 0, self.board)
            if piece is None:
                self._auto_resolve_no_move()
            else:
                self._try_move_piece(piece)

    def _on_roll_result(self, value: int) -> None:
        current_player = self.round_manager.current_player
        self.player_roll_counts[current_player.name] += 1
        self.current_roll = value
        self.last_dice_value = value
        self.last_dice_owner_name = current_player.name
        self.last_dice_color = self.player_colors.get(current_player.color, (240, 240, 240))
        if value == 6:
            self.consecutive_sixes += 1
        else:
            self.consecutive_sixes = 0

        if self.consecutive_sixes >= 3:
            self._notify("Tři šestky za sebou -> ztráta tahu", sticky=False, duration_ms=1700)
            self.next_turn()
            return

        player = self.round_manager.current_player
        self.valid_pieces = [piece for piece in player.pieces if self.board.is_valid_move(piece, value)]

        if not self.valid_pieces:
            self._auto_resolve_no_move()
            return

        self.awaiting_selection = True
        self._notify(
            f"{player.name}: padlo {value}. Vyber figurku klikem nebo klávesou 1-4",
            sticky=True,
        )

    def _auto_resolve_no_move(self) -> None:
        if self.current_roll == 6 and self.consecutive_sixes < 3:
            self.awaiting_selection = False
            self.current_roll = None
            self._notify(f"{self.round_manager.current_player.name}: žádná platná figurka. Hoď znovu.", sticky=True)
            return

        self._notify("Žádná platná figurka. Tah přeskočen.")
        self.next_turn()

    def _try_move_piece(self, piece) -> None:
        if not self.awaiting_selection:
            return
        if piece.owner is not self.round_manager.current_player:
            self.invalid_feedback_until = pygame.time.get_ticks() + 500
            return
        if piece not in self.valid_pieces:
            self.invalid_feedback_until = pygame.time.get_ticks() + 500
            return

        result = self.board.move_piece(piece, int(self.current_roll or 0))
        self.awaiting_selection = False
        self.valid_pieces.clear()

        if result == "captured":
            self.score_manager.add_points(piece.owner, "capture")
            self.renderer.draw_captured_animation(self.screen, piece)
            self._notify("Soupeřova figurka sebrána")
        elif result == "finished":
            self.score_manager.add_points(piece.owner, "finish_piece")
            self._notify("Figurka dokončila cíl")
        elif result == "moved":
            self._notify("Figurka posunuta")

        winner = self.check_win_condition()
        if winner is not None:
            self.end_game()
            return

        if self.current_roll == 6:
            self.current_roll = None
            self._notify(f"{piece.owner.name}: šestka -> házíš znovu", sticky=True)
            return

        self.next_turn()

    def _process_ai_turn(self) -> None:
        now = pygame.time.get_ticks()
        if now < self.ai_next_action_at:
            return

        if self.quiz_active:
            answer = random.randint(0, 2)
            self._handle_quiz_answer(answer)
            self.ai_next_action_at = now + 450
            return

        if self.quiz_feedback is not None:
            self.ai_next_action_at = now + 250
            return

        if not self.awaiting_selection:
            self._roll_dice()
        self.ai_next_action_at = now + 350

    def _handle_timeout_skip(self) -> None:
        self.pending_timeout_skip = False
        self.awaiting_selection = False
        self.valid_pieces.clear()
        self.quiz_active = False
        self.quiz_data = None
        self.quiz_option_rects = []
        self.quiz_pass_for = None
        self.quiz_feedback = None
        player = self.round_manager.current_player
        self.score_manager.apply_penalty(player, "timeout")
        self._notify("Vypršel čas tahu -> penalizace a přeskočení", sticky=False, duration_ms=1700)
        self.next_turn()

    def _restart_game(self) -> None:
        """Exit current match and return to the main setup menu."""
        self.return_to_main_menu = True
        self.running = False

    def _draw_frame(self) -> None:
        self.renderer.draw_background(self.screen)
        self.hud.set_panel_rect(self.renderer.hud_rect)

        current_player = self.round_manager.current_player
        self.renderer.draw_board(self.screen)
        self.renderer.draw_pieces(self.screen, self.players, current_player=current_player)
        if self.awaiting_selection:
            self.renderer.highlight_valid_moves(self.screen, self.valid_pieces)
        dice_value = self.current_roll if self.current_roll is not None else self.last_dice_value
        self.renderer.draw_dice(
            self.screen,
            dice_value,
            self.animating_roll,
            dice_color=self.last_dice_color,
            owner_name=self.last_dice_owner_name,
        )

        leaderboard = self.score_manager.get_leaderboard()
        self.hud.draw(
            self.screen,
            self.players,
            current_player,
            self.timer_manager,
            leaderboard,
            game_remaining_seconds=self._get_game_remaining_seconds(),
        )

        show_notification = self.notification_sticky
        if self.notification_until is not None:
            show_notification = show_notification or pygame.time.get_ticks() <= self.notification_until

        if show_notification:
            self.dialogs.draw_notification(self.screen, self.notification)

        if pygame.time.get_ticks() <= self.invalid_feedback_until:
            self.dialogs.draw_error_feedback(self.screen)

        if self.quiz_active and self.quiz_data is not None:
            self.quiz_option_rects = self.dialogs.draw_quiz_question(
                self.screen,
                player_name=self.quiz_data["player_name"],
                question=self.quiz_data["question"],
                options=self.quiz_data["options"],
            )
        else:
            self.quiz_option_rects = []

        if self.quiz_feedback is not None:
            self.dialogs.draw_quiz_result(
                self.screen,
                player_name=self.quiz_feedback["player_name"],
                is_correct=bool(self.quiz_feedback["is_correct"]),
            )

        helper = pygame.font.SysFont("arial", 20).render("Esc - pauza", True, (80, 80, 80))
        self.screen.blit(helper, (self.renderer.hud_rect.left + 20, self.renderer.hud_rect.bottom - 50))

        if self.round_manager.timed_out and self.animating_roll:
            self.dialogs.draw_notification(self.screen, "Čas vypršel během animace")

    def _notify(self, message: str, sticky: bool = True, duration_ms: int = 2200) -> None:
        self.notification = message
        self.notification_sticky = sticky
        self.notification_until = None if sticky else pygame.time.get_ticks() + duration_ms

    def _set_turn_instruction(self) -> None:
        """Set persistent bottom instruction for the current turn state."""
        player = self.round_manager.current_player
        self.last_dice_value = None
        self.last_dice_owner_name = None
        self.last_dice_color = (240, 240, 240)
        if player.is_ai:
            self._notify(f"Na tahu {player.name} ({player.color}) - AI přemýšlí...", sticky=True)
            return

        self._notify(
            f"Na tahu {player.name} ({player.color}) - stiskni MEZERNÍK pro hod kostkou",
            sticky=True,
        )

    def _safe_shutdown(self) -> None:
        self.timer_manager.stop()
        try:
            self.score_manager.save_scores()
        except Exception:
            logging.exception("Failed to save scores during shutdown")

    def _get_game_remaining_seconds(self) -> float:
        """Return remaining time for whole match timer."""
        elapsed = (pygame.time.get_ticks() - self.game_start_ticks) / 1000.0
        return max(0.0, self.GAME_DURATION_SECONDS - elapsed)

    def _is_game_time_over(self) -> bool:
        """Return True when whole match timer expires."""
        return self._get_game_remaining_seconds() <= 0

    def _pick_score_winner(self) -> Player | None:
        """Pick winner by in-game score when match timer expires."""
        if not self.players:
            return None

        return max(
            self.players,
            key=lambda player: (
                player.score,
                sum(1 for piece in player.pieces if piece.finished),
            ),
        )

    def _start_quiz(self, player: Player, roll_number: int) -> None:
        """Open a quiz gate that must be answered before specific rolls."""
        quiz = random.choice(self.quiz_bank)
        self.quiz_pass_for = None
        self.quiz_active = True
        self.quiz_data = {
            "player_name": player.name,
            "roll_number": roll_number,
            "question": quiz["question"],
            "options": quiz["options"],
            "correct": quiz["correct"],
        }
        self._notify(f"{player.name}: před {roll_number}. hodem odpověz na otázku (1-3)", sticky=True)

    def _handle_quiz_answer(self, selected_option: int) -> None:
        """Evaluate quiz answer; allow roll on success, skip turn on failure."""
        if not self.quiz_active or self.quiz_data is None:
            return

        player = self.round_manager.current_player
        roll_number = int(self.quiz_data["roll_number"])
        correct = int(self.quiz_data["correct"])

        self.quiz_active = False
        self.quiz_option_rects = []

        if selected_option == correct:
            self.score_manager.add_points(player, "quiz_correct")
            self.quiz_data = None
            self.quiz_feedback = {
                "player_name": player.name,
                "is_correct": True,
                "roll_number": roll_number,
                "until": pygame.time.get_ticks() + 1300,
            }
            return

        self.score_manager.apply_penalty(player, "quiz_wrong")
        self.quiz_data = None
        self.quiz_feedback = {
            "player_name": player.name,
            "is_correct": False,
            "roll_number": roll_number,
            "until": pygame.time.get_ticks() + 1300,
        }
        return

    def _update_quiz_feedback(self) -> None:
        """Resolve delayed action after showing quiz result overlay."""
        if self.quiz_feedback is None:
            return

        if pygame.time.get_ticks() <= int(self.quiz_feedback["until"]):
            return

        player = self.round_manager.current_player
        is_correct = bool(self.quiz_feedback["is_correct"])
        roll_number = int(self.quiz_feedback["roll_number"])
        self.quiz_feedback = None

        if is_correct:
            self.quiz_pass_for = (player.name, roll_number)
            self._notify("Správně! +10 bodů. Může se házet.", sticky=True)
            if player.is_ai:
                self._roll_dice()
            else:
                self._set_turn_instruction()
            return

        self.quiz_pass_for = None
        self._notify("Špatná odpověď. -5 bodů. Tah je přeskočen.", sticky=False, duration_ms=1700)
        self.next_turn()


def _run() -> None:
    pygame.init()
    display_info = pygame.display.Info()
    screen = pygame.display.set_mode((display_info.current_w, display_info.current_h), pygame.FULLSCREEN)
    pygame.display.set_caption("Člověče, nezlob se")

    menu = Menu(screen)
    config = menu.show_main_menu()
    game = Game(
        num_players=config["num_players"],
        ai_players=config["ai_players"],
        time_limit=config["time_limit"],
        player_names=config.get("player_names"),
    )
    game.start()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    _run()
