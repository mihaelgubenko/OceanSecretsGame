# -*- coding: utf-8 -*-
"""Процедурный LCD-рендерер игры «Тайны океана».

В модуле нет внешних изображений: корпус, экран, корабль, осьминог, водолаз,
сундук и семисегментное табло собираются только примитивами ``pygame.draw``.
"""

from __future__ import annotations

import math
from typing import Optional

import pygame

from game_logic import MODE_A, MODE_B, POS_BOAT


# Палитра стилизованного советского LCD-дисплея.
BODY_DARK = (24, 30, 38)
BODY_MID = (55, 65, 75)
BODY_LIGHT = (112, 122, 128)
LCD_BG = (184, 194, 184)          # #B8C2B8
LCD_SEGMENT = (30, 42, 56)        # #1E2A38
LCD_GHOST = (157, 171, 157)
LCD_GHOST_DARK = (138, 154, 142)
RED = (177, 52, 47)
RED_DARK = (111, 39, 39)
GOLD = (204, 151, 35)
GOLD_LIGHT = (237, 194, 80)
BLUE = (52, 102, 125)
WATER = (169, 184, 173)
WHITE = (224, 229, 224)


class LCDRenderer:
    """Отрисовка корпуса, ЖК-поля и процедурных игровых объектов."""

    SCREEN_RECT = pygame.Rect(94, 68, 812, 430)
    BUTTON_RECTS = {
        "left": pygame.Rect(64, 548, 116, 70),
        "mode_a": pygame.Rect(260, 558, 132, 54),
        "mode_b": pygame.Rect(414, 558, 132, 54),
        "time": pygame.Rect(568, 558, 132, 54),
        "right": pygame.Rect(820, 548, 116, 70),
    }

    # Крупные координаты водолаза в пространстве LCD.
    DIVER_POSITIONS = {
        0: (174, 145),
        1: (280, 215),
        2: (398, 286),
        3: (592, 375),
        4: (474, 305),
    }

    def __init__(self, size: tuple[int, int] = (1000, 650)):
        self.size = size
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_small = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_tiny = pygame.font.SysFont("Consolas", 12, bold=True)
        self.button_rects = {name: rect.copy() for name, rect in self.BUTTON_RECTS.items()}

    def button_at(self, position: tuple[int, int]) -> Optional[str]:
        """Вернуть имя аппаратной кнопки под курсором, если она нажата."""
        for name, rect in self.button_rects.items():
            if rect.collidepoint(position):
                return name
        return None

    def draw(
        self,
        surface: pygame.Surface,
        game,
        *,
        elapsed: float = 0.0,
        show_time: bool = False,
        muted: bool = False,
    ) -> None:
        surface.fill(BODY_DARK)
        self._draw_housing(surface)
        self._draw_lcd(surface)
        self._draw_score(surface, game, elapsed=elapsed, show_time=show_time)
        self._draw_background_scene(surface)
        self._draw_tentacles(surface, game.tentacles)
        self._draw_boat_and_lives(surface, game.lives)
        self._draw_ship_and_decorations(surface)
        self._draw_chest(surface)
        self._draw_diver(surface, game)
        self._draw_status(surface, game, muted=muted)
        self._draw_controls(surface, game.mode)

    def _draw_housing(self, surface: pygame.Surface) -> None:
        outer = pygame.Rect(16, 12, self.size[0] - 32, self.size[1] - 24)
        pygame.draw.rect(surface, BODY_MID, outer, border_radius=24)
        pygame.draw.rect(surface, BODY_LIGHT, outer, width=3, border_radius=24)
        pygame.draw.rect(surface, BODY_DARK, outer.inflate(-18, -18), width=3, border_radius=18)

        title = self.font_title.render("ЭЛЕКТРОНИКА  •  ТАЙНЫ ОКЕАНА", True, WHITE)
        surface.blit(title, (outer.centerx - title.get_width() // 2, 25))

        # Небольшие декоративные винты корпуса.
        for x, y in ((38, 35), (962, 35), (38, 620), (962, 620)):
            pygame.draw.circle(surface, BODY_DARK, (x, y), 7)
            pygame.draw.circle(surface, BODY_LIGHT, (x - 2, y - 2), 2)

    def _draw_lcd(self, surface: pygame.Surface) -> None:
        rect = self.SCREEN_RECT
        pygame.draw.rect(surface, (9, 14, 18), rect.inflate(10, 10), border_radius=14)
        pygame.draw.rect(surface, LCD_GHOST_DARK, rect.inflate(4, 4), border_radius=10)
        pygame.draw.rect(surface, LCD_BG, rect, border_radius=8)
        pygame.draw.rect(surface, LCD_SEGMENT, rect, width=2, border_radius=8)

        # Едва заметные горизонтальные линии стекла.
        for y in range(rect.top + 8, rect.bottom - 5, 9):
            pygame.draw.line(surface, (176, 187, 176), (rect.left + 5, y), (rect.right - 5, y), 1)

    def _draw_score(self, surface: pygame.Surface, game, *, elapsed: float, show_time: bool) -> None:
        # Неразборчивый ghost-табло рисуется первым, активные цифры — поверх.
        score = max(0, int(game.score)) % 10000
        digits = f"{score:04d}"
        x0, y0, width, height, gap = 468, 84, 28, 48, 9
        for index, char in enumerate(digits):
            self._draw_digit(surface, x0 + index * (width + gap), y0, width, height, char, active=True)

        dp = self.font_tiny.render("ДП", True, LCD_SEGMENT)
        pp = self.font_tiny.render("ПП", True, LCD_GHOST_DARK)
        surface.blit(dp, (454, 139))
        surface.blit(pp, (614, 139))

        label = self.font_small.render("СЧЁТ", True, LCD_SEGMENT)
        surface.blit(label, (376, 99))
        if show_time:
            minutes, seconds = divmod(max(0, int(elapsed)), 60)
            time_text = self.font_tiny.render(f"ВРЕМЯ {minutes:02d}:{seconds:02d}", True, LCD_SEGMENT)
            surface.blit(time_text, (730, 91))

    def _draw_digit(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
        digit: str,
        *,
        active: bool,
    ) -> None:
        thickness = 5
        mid = y + height // 2
        segments = {
            "a": ((x + 3, y + 3), (x + width - 3, y + 3)),
            "b": ((x + width - 3, y + 4), (x + width - 3, mid - 3)),
            "c": ((x + width - 3, mid + 3), (x + width - 3, y + height - 4)),
            "d": ((x + 3, y + height - 3), (x + width - 3, y + height - 3)),
            "e": ((x + 3, mid + 3), (x + 3, y + height - 4)),
            "f": ((x + 3, y + 4), (x + 3, mid - 3)),
            "g": ((x + 3, mid), (x + width - 3, mid)),
        }
        active_segments = {
            "0": "ab cdef".replace(" ", ""),
            "1": "bc",
            "2": "abdeg",
            "3": "abcdg",
            "4": "bcfg",
            "5": "acdfg",
            "6": "acdefg",
            "7": "abc",
            "8": "abcdefg",
            "9": "abcdfg",
        }.get(str(digit), "")
        for name, (start, end) in segments.items():
            pygame.draw.line(surface, LCD_GHOST, start, end, max(2, thickness - 2))
            if active and name in active_segments:
                pygame.draw.line(surface, LCD_SEGMENT, start, end, thickness)

    def _draw_background_scene(self, surface: pygame.Surface) -> None:
        # Волны и пузырьки оставляют ощущение прозрачного LCD-фона.
        for offset in (0, 26, 52):
            points = []
            for x in range(self.SCREEN_RECT.left + 10, self.SCREEN_RECT.right - 10, 12):
                y = 178 + offset + int(5 * math.sin(x / 32.0 + offset))
                points.append((x, y))
            pygame.draw.lines(surface, WATER, False, points, 2)
        for x, y, radius in ((752, 180, 4), (778, 213, 3), (720, 246, 2), (840, 302, 3)):
            pygame.draw.circle(surface, LCD_GHOST_DARK, (x, y), radius, width=1)

        # Маршрут водолаза в виде призрачной кабельной линии.
        route = [self.DIVER_POSITIONS[i] for i in (0, 1, 2, 3)]
        pygame.draw.lines(surface, LCD_GHOST, False, route, 2)
        pygame.draw.line(surface, RED_DARK, (171, 158), (171, 210), 2)

    def _draw_boat_and_lives(self, surface: pygame.Surface, lives: int) -> None:
        # Красная лодка в верхнем левом углу LCD.
        pygame.draw.polygon(surface, RED, [(122, 124), (220, 124), (207, 145), (145, 145)])
        pygame.draw.line(surface, RED_DARK, (132, 151), (203, 151), 3)
        pygame.draw.line(surface, RED, (173, 123), (173, 91), 3)
        pygame.draw.line(surface, RED, (173, 94), (205, 94), 2)
        pygame.draw.line(surface, RED, (204, 94), (204, 113), 2)
        pygame.draw.line(surface, RED_DARK, (173, 151), (174, 177), 2)

        for index in range(3):
            x = 143 + index * 27
            color = LCD_SEGMENT if index < lives else LCD_GHOST
            pygame.draw.circle(surface, color, (x, 107), 5)
            pygame.draw.line(surface, color, (x, 113), (x, 125), 3)
            pygame.draw.line(surface, color, (x, 116), (x - 6, 121), 2)
            pygame.draw.line(surface, color, (x, 116), (x + 6, 121), 2)
            pygame.draw.line(surface, color, (x, 125), (x - 5, 132), 2)
            pygame.draw.line(surface, color, (x, 125), (x + 5, 132), 2)

        label = self.font_tiny.render("ЖИЗНИ", True, LCD_SEGMENT)
        surface.blit(label, (124, 161))

    def _draw_ship_and_decorations(self, surface: pygame.Surface) -> None:
        # Затонувший корабль — красный оверлей поверх призрачного силуэта.
        ghost = LCD_GHOST
        pygame.draw.polygon(surface, ghost, [(350, 327), (475, 327), (510, 350), (335, 350)], width=2)
        pygame.draw.polygon(surface, RED, [(346, 318), (465, 318), (500, 340), (335, 340)])
        pygame.draw.line(surface, RED_DARK, (350, 340), (492, 340), 4)
        pygame.draw.line(surface, RED, (414, 318), (414, 256), 3)
        pygame.draw.line(surface, RED, (414, 258), (463, 278), 2)
        pygame.draw.line(surface, RED, (414, 272), (380, 292), 2)
        pygame.draw.line(surface, LCD_SEGMENT, (393, 328), (406, 328), 3)
        pygame.draw.line(surface, LCD_SEGMENT, (426, 328), (439, 328), 3)

        # Водоросли и якорь.
        for base_x in (255, 285, 720, 748):
            pygame.draw.arc(surface, LCD_GHOST_DARK, (base_x - 13, 326, 24, 68), 0.2, 2.8, 2)
        pygame.draw.line(surface, LCD_SEGMENT, (771, 328), (771, 379), 3)
        pygame.draw.line(surface, LCD_SEGMENT, (751, 378), (791, 378), 3)
        pygame.draw.arc(surface, LCD_SEGMENT, (751, 362, 40, 35), math.pi, 2 * math.pi, 3)

    def _draw_chest(self, surface: pygame.Surface) -> None:
        # Сундук внизу справа: золотой оверлей и ghost-контур крышки.
        pygame.draw.rect(surface, LCD_GHOST_DARK, (542, 385, 108, 43), width=2)
        pygame.draw.arc(surface, GOLD, (542, 362, 108, 55), math.pi, 2 * math.pi, 4)
        pygame.draw.rect(surface, GOLD, (542, 389, 108, 38))
        pygame.draw.line(surface, GOLD_LIGHT, (546, 397), (646, 397), 3)
        pygame.draw.rect(surface, GOLD_LIGHT, (587, 398, 18, 17))
        pygame.draw.circle(surface, GOLD, (596, 405), 3)
        pygame.draw.polygon(surface, GOLD_LIGHT, [(567, 392), (582, 375), (592, 392)])
        pygame.draw.polygon(surface, GOLD_LIGHT, [(613, 392), (628, 376), (638, 392)])

    def _draw_tentacles(self, surface: pygame.Surface, stages: list[int]) -> None:
        base = (691, 268)
        targets = [(285, 205), (405, 286), (486, 340), (585, 382)]
        for index, target in enumerate(targets):
            bx, by = base
            tx, ty = target
            points = []
            for segment in range(1, 4):
                ratio = segment / 3.0
                # Небольшой изгиб, чтобы щупальца не выглядели прямыми лучами.
                bend = (index - 1.5) * 7 * math.sin(ratio * math.pi)
                px = int(bx + (tx - bx) * ratio)
                py = int(by + (ty - by) * ratio + bend)
                points.append((px, py))
            previous = base
            for segment, point in enumerate(points, start=1):
                color = LCD_SEGMENT if segment <= stages[index] else LCD_GHOST
                pygame.draw.line(surface, color, previous, point, 6 if segment <= stages[index] else 3)
                pygame.draw.circle(surface, color, point, 5 if segment <= stages[index] else 3)
                previous = point
        pygame.draw.circle(surface, LCD_GHOST_DARK, base, 30, width=3)
        pygame.draw.circle(surface, LCD_SEGMENT, base, 17, width=4)
        pygame.draw.circle(surface, LCD_SEGMENT, (680, 260), 3)
        pygame.draw.circle(surface, LCD_SEGMENT, (702, 260), 3)

    def _draw_diver(self, surface: pygame.Surface, game) -> None:
        position = self.DIVER_POSITIONS.get(game.diver_pos, self.DIVER_POSITIONS[POS_BOAT])
        if game.is_caught:
            color = RED if int(game.caught_timer * 8) % 2 else LCD_SEGMENT
        else:
            color = LCD_SEGMENT
        x, y = position
        pygame.draw.circle(surface, color, (x, y - 13), 7)
        pygame.draw.line(surface, color, (x, y - 5), (x, y + 18), 4)
        pygame.draw.line(surface, color, (x, y), (x - 13, y + 8), 3)
        pygame.draw.line(surface, color, (x, y), (x + 13, y + 8), 3)
        pygame.draw.line(surface, color, (x, y + 17), (x - 10, y + 29), 3)
        pygame.draw.line(surface, color, (x, y + 17), (x + 10, y + 29), 3)
        pygame.draw.line(surface, color, (x + 7, y - 7), (x + 13, y - 7), 2)
        if game.has_gold:
            pygame.draw.circle(surface, GOLD, (x + 14, y + 16), 6)

    def _draw_status(self, surface: pygame.Surface, game, *, muted: bool) -> None:
        if game.is_game_over:
            text = "КОНЕЦ ИГРЫ  •  ПРОБЕЛ — НОВАЯ ИГРА"
            color = RED
        elif game.is_caught:
            text = "ОПАСНОСТЬ!  •  ВОДОЛАЗ ПОЙМАН"
            color = RED
        elif game.has_gold:
            text = f"КЛАД В МЕШКЕ: {game.gold_in_sack}  •  ВЕРНИТЕСЬ В ЛОДКУ"
            color = GOLD
        else:
            text = "СТРЕЛКИ — ДВИЖЕНИЕ  •  A/B — РЕЖИМ  •  ПРОБЕЛ — СТАРТ"
            color = LCD_SEGMENT
        rendered = self.font_tiny.render(text, True, color)
        surface.blit(rendered, (self.SCREEN_RECT.centerx - rendered.get_width() // 2, 474))
        sound = self.font_tiny.render("ЗВУК: ВЫКЛ" if muted else "ЗВУК: ВКЛ", True, LCD_SEGMENT)
        surface.blit(sound, (self.SCREEN_RECT.right - sound.get_width() - 12, 82))

    def _draw_controls(self, surface: pygame.Surface, mode: str) -> None:
        for name, rect in self.button_rects.items():
            pygame.draw.rect(surface, BODY_DARK, rect, border_radius=12)
            pygame.draw.rect(surface, BODY_LIGHT, rect, width=2, border_radius=12)
            if name == "left":
                label = "◀"
                font = self.font_title
            elif name == "right":
                label = "▶"
                font = self.font_title
            else:
                labels = {"mode_a": "ИГРА А", "mode_b": "ИГРА Б", "time": "ВРЕМЯ"}
                label = labels[name]
                font = self.font_label
            color = GOLD_LIGHT if (name == "mode_a" and mode == MODE_A) or (name == "mode_b" and mode == MODE_B) else WHITE
            rendered = font.render(label, True, color)
            surface.blit(rendered, (rect.centerx - rendered.get_width() // 2, rect.centery - rendered.get_height() // 2))

