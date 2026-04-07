from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from game.piece import Piece
    from game.player import Player


class Renderer:
    """Renders board, pawns and simple effects using Pygame."""

    BOARD_SIZE = 700
    HUD_WIDTH = 340
    HUD_HEIGHT = 700
    LAYOUT_GAP = 24
    CELL_SIZE = 50
    PIECE_RADIUS = 15

    COLORS = {
        "red": (205, 60, 60),
        "blue": (65, 108, 210),
        "green": (50, 165, 92),
        "yellow": (230, 193, 58),
    }

    ENTRY_CELLS = {
        "red": 39,
        "blue": 9,
        "green": 19,
        "yellow": 29,
    }

    def __init__(self, safe_cells: list[int]) -> None:
        self.safe_cells = set(safe_cells)
        self.board_rect = pygame.Rect(0, 0, self.BOARD_SIZE, self.BOARD_SIZE)
        self.hud_rect = pygame.Rect(0, 0, self.HUD_WIDTH, self.HUD_HEIGHT)
        self.dice_rect = pygame.Rect(0, 0, 120, 120)
        self.track_points: list[tuple[int, int]] = []
        self.home_positions: dict[str, list[tuple[int, int]]] = {}
        self.goal_positions: dict[str, list[tuple[int, int]]] = {}
        self.font = pygame.font.SysFont("verdana", 20, bold=True)
        self.small_font = pygame.font.SysFont("verdana", 14, bold=True)
        self._last_piece_positions: list[tuple[Piece, tuple[int, int]]] = []
        self._last_surface_size: tuple[int, int] | None = None

    def draw_background(self, surface: pygame.Surface) -> None:
        """Draw textured gradient background for the whole scene."""
        self.update_layout(surface.get_size())
        width, height = surface.get_size()
        top = pygame.Color(255, 184, 121)
        bottom = pygame.Color(82, 130, 210)

        for y in range(height):
            ratio = y / max(1, height - 1)
            r = int(top.r + (bottom.r - top.r) * ratio)
            g = int(top.g + (bottom.g - top.g) * ratio)
            b = int(top.b + (bottom.b - top.b) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))

        for x in range(0, width, 36):
            pygame.draw.line(surface, (255, 255, 255, 20), (x, 0), (x - 140, height), 1)

        glow = pygame.Surface((480, 480), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 240, 174, 36), (240, 240), 210)
        pygame.draw.circle(glow, (255, 120, 132, 24), (180, 170), 120)
        surface.blit(glow, (self.board_rect.left + 80, self.board_rect.top + 80))

        side_glow = pygame.Surface((360, 360), pygame.SRCALPHA)
        pygame.draw.circle(side_glow, (107, 223, 155, 36), (180, 180), 150)
        surface.blit(side_glow, (self.hud_rect.left - 60, self.hud_rect.top + 120))

    def update_layout(self, surface_size: tuple[int, int]) -> None:
        """Recompute board and HUD layout to keep scene centered on any resolution."""
        if self._last_surface_size == surface_size:
            return

        width, height = surface_size
        total_width = self.BOARD_SIZE + self.LAYOUT_GAP + self.HUD_WIDTH
        total_height = max(self.BOARD_SIZE, self.HUD_HEIGHT)

        origin_x = max(12, (width - total_width) // 2)
        origin_y = max(12, (height - total_height) // 2)

        self.board_rect = pygame.Rect(origin_x, origin_y, self.BOARD_SIZE, self.BOARD_SIZE)
        self.hud_rect = pygame.Rect(self.board_rect.right + self.LAYOUT_GAP, origin_y, self.HUD_WIDTH, self.HUD_HEIGHT)
        self.dice_rect = pygame.Rect(self.board_rect.left - 140, self.board_rect.top + 20, 120, 120)

        self.track_points = self._build_track_points()
        self.home_positions = self._build_home_positions()
        self.goal_positions = self._build_goal_positions()
        self._last_surface_size = surface_size

    def draw_board(self, surface: pygame.Surface) -> None:
        """Draw board background, route cells and special markers."""
        self.update_layout(surface.get_size())
        board_bg = pygame.Surface((self.BOARD_SIZE, self.BOARD_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(board_bg, (244, 240, 224, 248), board_bg.get_rect(), border_radius=20)
        surface.blit(board_bg, self.board_rect.topleft)
        pygame.draw.rect(surface, (28, 30, 34), self.board_rect, width=3, border_radius=20)

        zones = {
            "red": pygame.Rect(self.board_rect.left + 80, self.board_rect.top + 80, 200, 200),
            "blue": pygame.Rect(self.board_rect.left + 445, self.board_rect.top + 80, 200, 200),
            "green": pygame.Rect(self.board_rect.left + 445, self.board_rect.top + 445, 200, 200),
            "yellow": pygame.Rect(self.board_rect.left + 80, self.board_rect.top + 445, 200, 200),
        }
        for color_name, rect in zones.items():
            tone = self.COLORS[color_name]
            fill = (tone[0], tone[1], tone[2], 52)
            overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(overlay, fill, overlay.get_rect(), border_radius=20)
            surface.blit(overlay, rect.topleft)
            pygame.draw.rect(surface, tone, rect, width=3, border_radius=20)

        for index, center in enumerate(self.track_points):
            rect = pygame.Rect(0, 0, self.CELL_SIZE, self.CELL_SIZE)
            rect.center = center
            cell_color = (255, 255, 255)
            entry_color = self._entry_color_for_cell(index)
            if entry_color is not None:
                cell_color = (
                    min(255, entry_color[0] + 26),
                    min(255, entry_color[1] + 26),
                    min(255, entry_color[2] + 26),
                )
            if index in self.safe_cells:
                cell_color = (251, 242, 178)
            pygame.draw.rect(surface, cell_color, rect, border_radius=9)
            pygame.draw.rect(surface, (84, 84, 84), rect, width=2, border_radius=9)

            if entry_color is not None:
                pygame.draw.rect(surface, entry_color, rect.inflate(-8, -8), width=2, border_radius=6)

            if index in self.safe_cells:
                star = self.font.render("*", True, (58, 54, 30))
                surface.blit(star, star.get_rect(center=(center[0], center[1] - 2)))

            if entry_color is not None:
                marker = self.small_font.render("C", True, (20, 20, 20))
                surface.blit(marker, marker.get_rect(center=(center[0], center[1] + 12)))

        center_rect = pygame.Rect(0, 0, 130, 130)
        center_rect.center = self.board_rect.center
        pygame.draw.rect(surface, (252, 249, 239), center_rect, border_radius=14)
        pygame.draw.rect(surface, (70, 70, 70), center_rect, width=2, border_radius=14)
        trophy = self.small_font.render("CÍL", True, (32, 32, 32))
        surface.blit(trophy, trophy.get_rect(center=center_rect.center))

        for color_name, positions in self.home_positions.items():
            color = self.COLORS[color_name]
            for home_cell in positions:
                pygame.draw.circle(surface, (245, 245, 245), home_cell, 18)
                pygame.draw.circle(surface, color, home_cell, 17, width=3)

        for color_name, lane in self.goal_positions.items():
            color = self.COLORS[color_name]
            for point in lane:
                pygame.draw.circle(surface, (245, 245, 245), point, 14)
                pygame.draw.circle(surface, color, point, 13, width=3)

    def draw_pieces(
        self,
        surface: pygame.Surface,
        players: list[Player],
        current_player: Player | None = None,
    ) -> None:
        """Draw all player pieces and remember screen coordinates for hit testing."""
        self._last_piece_positions.clear()
        stack_counts: dict[tuple[str, int], int] = defaultdict(int)

        for player in players:
            color = self.COLORS[player.color]
            for piece in player.pieces:
                key = self._stack_key(piece)
                stack_index = stack_counts[key]
                stack_counts[key] += 1
                center = self._piece_center(piece, stack_index)
                self._last_piece_positions.append((piece, center))

                if current_player is not None and piece.owner is current_player and not piece.finished:
                    pygame.draw.circle(surface, (255, 255, 255), center, self.PIECE_RADIUS + 7)
                    pygame.draw.circle(surface, self.COLORS[current_player.color], center, self.PIECE_RADIUS + 4, 2)

                pygame.draw.circle(surface, color, center, self.PIECE_RADIUS)
                pygame.draw.circle(surface, (20, 20, 20), center, self.PIECE_RADIUS, width=2)
                label = self.font.render(str(piece.piece_id + 1), True, (20, 20, 20))
                surface.blit(label, label.get_rect(center=center))

    def draw_dice(
        self,
        surface: pygame.Surface,
        value: int | None,
        animating: bool,
        dice_color: tuple[int, int, int] | None = None,
        owner_name: str | None = None,
    ) -> None:
        """Draw dice panel and current value."""
        panel = self.dice_rect
        tint = dice_color or (240, 240, 240)
        face_color = (
            min(255, tint[0] + 30),
            min(255, tint[1] + 30),
            min(255, tint[2] + 30),
        )
        pygame.draw.rect(surface, face_color, panel, border_radius=12)
        pygame.draw.rect(surface, (36, 38, 44), panel, width=3, border_radius=12)

        display_text = "..." if animating else ("-" if value is None else str(value))
        label = pygame.font.SysFont("verdana", 42, bold=True).render(display_text, True, (20, 20, 20))
        surface.blit(label, label.get_rect(center=panel.center))

        title = self.small_font.render("Kostka", True, (235, 235, 235))
        surface.blit(title, (panel.left + 22, panel.top - 26))

        if value is not None:
            last_roll = self.small_font.render(f"Poslední hod: {value}", True, (235, 235, 235))
            surface.blit(last_roll, (panel.left + 22, panel.top - 48))

        if owner_name:
            owner = self.small_font.render(owner_name, True, (235, 235, 235))
            surface.blit(owner, (panel.left + 22, panel.bottom + 8))

    def highlight_valid_moves(self, surface: pygame.Surface, pieces: list[Piece]) -> None:
        """Highlight selectable pieces."""
        for piece in pieces:
            center = self._find_piece_center(piece)
            if center is None:
                continue
            pygame.draw.circle(surface, (255, 250, 125), center, self.PIECE_RADIUS + 8, width=4)

    def draw_captured_animation(self, surface: pygame.Surface, piece: Piece) -> None:
        """Draw lightweight capture pulse animation."""
        center = self._find_piece_center(piece)
        if center is None:
            return

        for radius in (22, 30, 38):
            pygame.draw.circle(surface, (255, 80, 80), center, radius, width=2)
            pygame.display.flip()
            pygame.time.delay(40)

    def get_piece_at_pixel(self, position: tuple[int, int]) -> Piece | None:
        """Return clicked piece based on last rendered coordinates."""
        x, y = position
        for piece, center in reversed(self._last_piece_positions):
            dx = center[0] - x
            dy = center[1] - y
            if dx * dx + dy * dy <= (self.PIECE_RADIUS + 6) ** 2:
                return piece
        return None

    def _find_piece_center(self, target_piece: Piece) -> tuple[int, int] | None:
        """Return last drawn center for a specific piece instance."""
        for piece, center in self._last_piece_positions:
            if piece is target_piece:
                return center
        return None

    def _piece_center(self, piece: Piece, stack_index: int) -> tuple[int, int]:
        if piece.is_at_home():
            base = self.home_positions[piece.owner.color][piece.piece_id]
            return (base[0], base[1])

        if piece.position >= 40:
            lane_index = max(0, min(3, piece.position - 40))
            base = self.goal_positions[piece.owner.color][lane_index]
            return (base[0] + 8 * stack_index, base[1])

        base = self.track_points[piece.position]
        offset_x = (stack_index % 2) * 10
        offset_y = (stack_index // 2) * 10
        return (base[0] + offset_x, base[1] + offset_y)

    def _stack_key(self, piece: Piece) -> tuple[str, int]:
        if piece.is_at_home():
            return ("home", piece.piece_id)
        return (piece.owner.color, piece.position)

    def _build_track_points(self) -> list[tuple[int, int]]:
        left = self.board_rect.left + 50
        top = self.board_rect.top + 50
        right = self.board_rect.right - 30
        bottom = self.board_rect.bottom - 30
        points: list[tuple[int, int]] = []

        for i in range(10):
            points.append((left + i * 60, top))
        for i in range(10):
            points.append((right, top + i * 60))
        for i in range(10):
            points.append((right - i * 60, bottom))
        for i in range(10):
            points.append((left, bottom - i * 60))
        return points

    def _build_home_positions(self) -> dict[str, list[tuple[int, int]]]:
        ox = self.board_rect.left
        oy = self.board_rect.top
        return {
            "red": [(ox + 140, oy + 140), (ox + 220, oy + 140), (ox + 140, oy + 220), (ox + 220, oy + 220)],
            "blue": [(ox + 520, oy + 140), (ox + 600, oy + 140), (ox + 520, oy + 220), (ox + 600, oy + 220)],
            "green": [(ox + 520, oy + 520), (ox + 600, oy + 520), (ox + 520, oy + 600), (ox + 600, oy + 600)],
            "yellow": [(ox + 140, oy + 520), (ox + 220, oy + 520), (ox + 140, oy + 600), (ox + 220, oy + 600)],
        }

    def _build_goal_positions(self) -> dict[str, list[tuple[int, int]]]:
        cx, cy = self.board_rect.center
        return {
            # One centered shape: each color has its own lane toward the center, offset to avoid overlap.
            "red": [(cx - 170, cy - 20), (cx - 130, cy - 20), (cx - 90, cy - 20), (cx - 50, cy - 20)],
            "blue": [(cx + 20, cy - 170), (cx + 20, cy - 130), (cx + 20, cy - 90), (cx + 20, cy - 50)],
            "green": [(cx + 170, cy + 20), (cx + 130, cy + 20), (cx + 90, cy + 20), (cx + 50, cy + 20)],
            "yellow": [(cx - 20, cy + 170), (cx - 20, cy + 130), (cx - 20, cy + 90), (cx - 20, cy + 50)],
        }

    def _entry_color_for_cell(self, cell_index: int) -> tuple[int, int, int] | None:
        """Return team color for an entry-to-goal cell on the track."""
        for color_name, entry_index in self.ENTRY_CELLS.items():
            if cell_index == entry_index:
                return self.COLORS[color_name]
        return None
