# -*- coding: utf-8 -*-
"""Процедурный LCD-рендерер в духе советской игры «Тайны океана».

Корпус и игровые объекты рисуются примитивами pygame. Внешние изображения
не используются: фотография ИМ-03 служит только визуальным референсом.
"""

from __future__ import annotations

import math
from typing import Optional

import pygame

from game_logic import MODE_A, MODE_B, POS_BOAT


# Тёплая пластмасса корпуса и красная окантовка оригинальной компоновки.
BODY_CREAM = (235, 230, 208)
BODY_CREAM_DARK = (196, 185, 156)
BODY_SHADOW = (151, 140, 116)
BODY_RED = (166, 43, 49)
BODY_RED_DARK = (112, 31, 37)
BODY_RED_LIGHT = (205, 73, 78)
INK = (28, 35, 39)

# Палитра сегментного ЖК-экрана из ТЗ.
LCD_BG = (184, 194, 184)          # #B8C2B8
LCD_SEGMENT = (30, 42, 56)        # #1E2A38
LCD_GHOST = (155, 169, 154)
LCD_GHOST_DARK = (132, 149, 135)
GOLD = (191, 143, 34)
GOLD_LIGHT = (224, 183, 68)
WATER = (153, 173, 158)
WHITE = (250, 248, 235)


class LCDRenderer:
    """Отрисовка корпуса, экрана, LCD-объектов и аппаратных кнопок."""

    # Схема корпуса повторяет эталонную фотографию: LCD по центру,
    # стрелочные кнопки по бокам, три овальные кнопки справа.
    SCREEN_RECT = pygame.Rect(216, 137, 552, 314)
    BEZEL_RECT = pygame.Rect(184, 82, 616, 423)
    BUTTON_RECTS = {
        "left": pygame.Rect(63, 365, 92, 92),
        "mode_a": pygame.Rect(850, 105, 48, 28),
        "mode_b": pygame.Rect(850, 174, 48, 28),
        "time": pygame.Rect(850, 243, 48, 28),
        "right": pygame.Rect(845, 365, 92, 92),
    }

    # Координаты в локальной системе LCD, чтобы композиция масштабировалась
    # вместе с экраном, а не зависела от внешнего корпуса.
    DIVER_POSITIONS = {
        0: (74, 70),
        1: (178, 132),
        2: (274, 202),
        3: (424, 262),
        4: (335, 205),
    }

    def __init__(self, size: tuple[int, int] = (1000, 650)):
        self.size = size
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_small = pygame.font.SysFont("Arial", 13, bold=True)
        self.font_label = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_brand = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_tiny = pygame.font.SysFont("Consolas", 11, bold=True)
        self.button_rects = {name: rect.copy() for name, rect in self.BUTTON_RECTS.items()}

    def button_at(self, position: tuple[int, int]) -> Optional[str]:
        """Вернуть имя кнопки под курсором."""
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
        clock_info: Optional[tuple[int, int, str]] = None,
        muted: bool = False,
    ) -> None:
        surface.fill(BODY_RED_DARK)
        self._draw_housing(surface)
        self._draw_lcd(surface)
        self._draw_score(surface, game, show_time=show_time, clock_info=clock_info)
        self._draw_underwater_scene(surface)
        self._draw_tentacles(surface, game.tentacles)
        self._draw_boat_and_lives(surface, game.lives)
        self._draw_ship(surface)
        self._draw_chest(surface)
        self._draw_diver(surface, game)
        self._draw_status(surface, game, show_time=show_time, muted=muted)
        self._draw_controls(surface, game.mode, show_time=show_time)

    def _draw_housing(self, surface: pygame.Surface) -> None:
        outer = pygame.Rect(15, 12, self.size[0] - 30, self.size[1] - 24)
        pygame.draw.rect(surface, BODY_CREAM, outer, border_radius=22)
        pygame.draw.rect(surface, BODY_RED, outer, width=5, border_radius=22)
        pygame.draw.rect(surface, BODY_CREAM_DARK, outer.inflate(-22, -22), width=2, border_radius=17)

        # Логотип слева — стилизованные инициалы, без копирования растрового знака.
        logo = pygame.Rect(46, 76, 92, 78)
        pygame.draw.rect(surface, BODY_CREAM_DARK, logo, border_radius=5)
        pygame.draw.rect(surface, INK, logo, width=2, border_radius=5)
        pygame.draw.circle(surface, INK, logo.center, 27, width=2)
        logo_text = self.font_brand.render("ИМ", True, INK)
        surface.blit(logo_text, (logo.centerx - logo_text.get_width() // 2, logo.centery - logo_text.get_height() // 2))

        # Название над индикатором и фирменная подпись под ним.
        brand = self.font_brand.render("электроника", True, INK)
        surface.blit(brand, (self.BEZEL_RECT.centerx - brand.get_width() // 2, 510))

        # Три небольших светлых винта/углубления корпуса.
        for x, y in ((30, 30), (970, 30), (30, 620), (970, 620)):
            pygame.draw.circle(surface, BODY_SHADOW, (x, y), 6)
            pygame.draw.circle(surface, BODY_CREAM, (x - 2, y - 2), 2)

    def _draw_lcd(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, BODY_RED_DARK, self.BEZEL_RECT.inflate(8, 8), border_radius=9)
        pygame.draw.rect(surface, BODY_RED, self.BEZEL_RECT.inflate(3, 3), border_radius=7)
        pygame.draw.rect(surface, BODY_CREAM_DARK, self.BEZEL_RECT, border_radius=5)
        pygame.draw.rect(surface, BODY_RED_DARK, self.SCREEN_RECT.inflate(11, 11), border_radius=6)
        pygame.draw.rect(surface, LCD_BG, self.SCREEN_RECT, border_radius=3)
        pygame.draw.rect(surface, INK, self.SCREEN_RECT, width=2, border_radius=3)

        title = self.font_label.render("ТАЙНЫ ОКЕАНА", True, INK)
        surface.blit(title, (self.BEZEL_RECT.centerx - title.get_width() // 2, 94))

        # Едва заметная сетка стекла, как на старом сегментном индикаторе.
        for y in range(self.SCREEN_RECT.top + 5, self.SCREEN_RECT.bottom - 3, 8):
            pygame.draw.line(
                surface,
                (174, 185, 174),
                (self.SCREEN_RECT.left + 4, y),
                (self.SCREEN_RECT.right - 4, y),
                1,
            )

    def _screen_point(self, x: int, y: int) -> tuple[int, int]:
        return self.SCREEN_RECT.left + x, self.SCREEN_RECT.top + y

    def _draw_score(
        self,
        surface: pygame.Surface,
        game,
        *,
        show_time: bool,
        clock_info: Optional[tuple[int, int, str]],
    ) -> None:
        if show_time and clock_info is not None:
            hour, minute, period = clock_info
            digits = f"{hour:02d}{minute:02d}"
        else:
            digits = f"{max(0, int(game.score)) % 10000:04d}"
            period = "ДП"

        x0 = self.SCREEN_RECT.left + 244
        y0 = self.SCREEN_RECT.top + 13
        for index, digit in enumerate(digits):
            self._draw_digit(surface, x0 + index * 31, y0, 24, 45, digit)
            if show_time and index == 1:
                pygame.draw.circle(surface, LCD_SEGMENT, (x0 + index * 31 + 29, y0 + 15), 2)
                pygame.draw.circle(surface, LCD_SEGMENT, (x0 + index * 31 + 29, y0 + 31), 2)

        label = self.font_tiny.render("ВРЕМЯ" if show_time else "СЧЁТ", True, LCD_SEGMENT)
        surface.blit(label, self._screen_point(214, 25))
        dp = self.font_tiny.render(period if show_time else "ДП", True, LCD_SEGMENT)
        pp_color = LCD_SEGMENT if show_time and period == "ПП" else LCD_GHOST_DARK
        pp = self.font_tiny.render("ПП", True, pp_color)
        surface.blit(dp, self._screen_point(224, 59))
        surface.blit(pp, self._screen_point(270, 59))

    def _draw_digit(self, surface: pygame.Surface, x: int, y: int, width: int, height: int, digit: str) -> None:
        thickness = 4
        middle = y + height // 2
        segments = {
            "a": ((x + 3, y + 3), (x + width - 3, y + 3)),
            "b": ((x + width - 3, y + 4), (x + width - 3, middle - 3)),
            "c": ((x + width - 3, middle + 3), (x + width - 3, y + height - 4)),
            "d": ((x + 3, y + height - 3), (x + width - 3, y + height - 3)),
            "e": ((x + 3, middle + 3), (x + 3, y + height - 4)),
            "f": ((x + 3, y + 4), (x + 3, middle - 3)),
            "g": ((x + 3, middle), (x + width - 3, middle)),
        }
        enabled = {
            "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg",
            "4": "bcfg", "5": "acdfg", "6": "acdefg", "7": "abc",
            "8": "abcdefg", "9": "abcdfg",
        }.get(str(digit), "")
        for name, (start, end) in segments.items():
            pygame.draw.line(surface, LCD_GHOST, start, end, max(2, thickness - 2))
            if name in enabled:
                pygame.draw.line(surface, LCD_SEGMENT, start, end, thickness)

    def _draw_underwater_scene(self, surface: pygame.Surface) -> None:
        # Поверхность воды и тонкие волны в верхней части индикатора.
        for row in range(3):
            points = []
            for x in range(6, self.SCREEN_RECT.width - 6, 12):
                y = 52 + row * 15 + int(3 * math.sin(x / 24 + row))
                points.append(self._screen_point(x, y))
            pygame.draw.lines(surface, WATER, False, points, 2)

        # Пузырьки, рыбы и водоросли создают живой подводный фон. Это
        # декоративная флора и фауна, а не подсказка опасных зон.
        for x, y, radius in ((83, 170, 3), (105, 199, 2), (487, 127, 3), (515, 160, 2)):
            pygame.draw.circle(surface, LCD_GHOST_DARK, self._screen_point(x, y), radius, width=1)

        for x, y, direction in ((112, 126, 1), (385, 115, -1), (505, 205, 1)):
            fx, fy = self._screen_point(x, y)
            pygame.draw.ellipse(surface, LCD_GHOST_DARK, (fx - 10, fy - 4, 20, 8), width=2)
            if direction > 0:
                tail = [(fx - 9, fy), (fx - 18, fy - 7), (fx - 18, fy + 7)]
            else:
                tail = [(fx + 9, fy), (fx + 18, fy - 7), (fx + 18, fy + 7)]
            pygame.draw.polygon(surface, LCD_GHOST_DARK, tail)
            pygame.draw.circle(surface, LCD_GHOST_DARK, (fx + 5 * direction, fy - 1), 1)

        for x, y in ((62, 292), (95, 288), (480, 292), (509, 286)):
            points = []
            for step in range(6):
                points.append(self._screen_point(x + int(7 * math.sin(step / 2)), y - step * 9))
            pygame.draw.lines(surface, LCD_GHOST_DARK, False, points, 2)

    def _draw_boat_and_lives(self, surface: pygame.Surface, lives: int) -> None:
        ox, oy = self._screen_point(24, 39)
        pygame.draw.polygon(surface, BODY_RED, [(ox, oy + 8), (ox + 87, oy + 8), (ox + 72, oy + 27), (ox + 16, oy + 27)])
        pygame.draw.line(surface, BODY_RED_DARK, (ox + 7, oy + 32), (ox + 80, oy + 32), 3)
        pygame.draw.line(surface, BODY_RED, (ox + 42, oy + 8), (ox + 42, oy - 12), 2)

        # Три компактных шлема вместо повторения полноразмерных человечков.
        for index in range(3):
            x, y = self._screen_point(27 + index * 25, 23)
            color = LCD_SEGMENT if index < lives else LCD_GHOST
            pygame.draw.circle(surface, color, (x, y), 5, width=2)
            pygame.draw.arc(surface, color, (x - 7, y - 7, 14, 14), math.pi, 2 * math.pi, 2)

    def _draw_ship(self, surface: pygame.Surface) -> None:
        # Затонувший корабль справа: красный цвет — цветной overlay, остальное LCD.
        x, y = self._screen_point(445, 180)
        pygame.draw.polygon(surface, LCD_GHOST_DARK, [(x - 4, y + 28), (x + 108, y + 28), (x + 130, y + 48), (x - 18, y + 48)], width=2)
        pygame.draw.polygon(surface, BODY_RED, [(x, y + 20), (x + 104, y + 20), (x + 126, y + 39), (x - 16, y + 39)])
        pygame.draw.line(surface, BODY_RED_DARK, (x - 7, y + 39), (x + 121, y + 39), 4)
        pygame.draw.line(surface, BODY_RED, (x + 42, y + 20), (x + 42, y - 45), 3)
        pygame.draw.line(surface, BODY_RED, (x + 42, y - 42), (x + 91, y - 21), 2)
        pygame.draw.line(surface, BODY_RED, (x + 42, y - 30), (x + 10, y - 12), 2)
        pygame.draw.line(surface, LCD_SEGMENT, (x + 22, y + 30), (x + 34, y + 30), 3)
        pygame.draw.line(surface, LCD_SEGMENT, (x + 63, y + 30), (x + 75, y + 30), 3)

    def _draw_chest(self, surface: pygame.Surface) -> None:
        x, y = self._screen_point(405, 255)
        pygame.draw.rect(surface, LCD_GHOST_DARK, (x - 3, y + 7, 104, 38), width=2)
        pygame.draw.arc(surface, GOLD, (x - 3, y - 16, 104, 52), math.pi, 2 * math.pi, 4)
        pygame.draw.rect(surface, GOLD, (x, y + 10, 98, 35))
        pygame.draw.line(surface, GOLD_LIGHT, (x + 3, y + 18), (x + 95, y + 18), 3)
        pygame.draw.rect(surface, GOLD_LIGHT, (x + 43, y + 19, 16, 15))
        pygame.draw.circle(surface, GOLD, (x + 51, y + 26), 3)
        pygame.draw.polygon(surface, GOLD_LIGHT, [(x + 22, y + 11), (x + 37, y - 6), (x + 48, y + 11)])
        pygame.draw.polygon(surface, GOLD_LIGHT, [(x + 65, y + 11), (x + 80, y - 6), (x + 91, y + 11)])

    def _draw_tentacles(self, surface: pygame.Surface, stages: list[int]) -> None:
        base = self._screen_point(355, 112)
        # Четыре атакующих направления: позиции 1, 2, 2 и 3.
        # При stage=0 ничего не рисуем — игрок не видит будущую траекторию.
        targets = [(178, 132), (270, 202), (292, 214), (424, 262)]
        for index, target in enumerate(targets):
            if stages[index] <= 0:
                continue
            points = [base]
            tx, ty = self._screen_point(*target)
            bx, by = base
            for segment in range(1, 4):
                ratio = segment / 3.0
                bend = (index - 1.5) * 10 * math.sin(ratio * math.pi)
                points.append((int(bx + (tx - bx) * ratio), int(by + (ty - by) * ratio + bend)))
            active_points = points[: stages[index] + 1]
            pygame.draw.lines(surface, LCD_SEGMENT, False, active_points, 7)
            pygame.draw.circle(surface, LCD_SEGMENT, active_points[-1], 5)

        # Крупная цельная голова осьминога.
        head = pygame.Rect(base[0] - 53, base[1] - 48, 106, 74)
        pygame.draw.ellipse(surface, LCD_GHOST_DARK, head, width=3)
        pygame.draw.ellipse(surface, LCD_SEGMENT, head.inflate(-8, -6))
        pygame.draw.circle(surface, LCD_BG, (base[0] - 18, base[1] - 18), 7)
        pygame.draw.circle(surface, LCD_BG, (base[0] + 18, base[1] - 18), 7)
        pygame.draw.circle(surface, LCD_SEGMENT, (base[0] - 18, base[1] - 18), 2)
        pygame.draw.circle(surface, LCD_SEGMENT, (base[0] + 18, base[1] - 18), 2)
        pygame.draw.arc(surface, LCD_BG, (base[0] - 22, base[1] - 5, 44, 20), 0.2, 2.9, 3)

    def _draw_diver(self, surface: pygame.Surface, game) -> None:
        if game.diver_pos == POS_BOAT:
            return
        x, y = self._screen_point(*self.DIVER_POSITIONS.get(game.diver_pos, self.DIVER_POSITIONS[POS_BOAT]))
        color = BODY_RED if game.is_caught and int(game.caught_timer * 8) % 2 else LCD_SEGMENT
        pygame.draw.circle(surface, color, (x, y - 13), 6)
        pygame.draw.line(surface, color, (x, y - 6), (x, y + 17), 4)
        pygame.draw.line(surface, color, (x, y), (x - 12, y + 8), 3)
        pygame.draw.line(surface, color, (x, y), (x + 12, y + 8), 3)
        pygame.draw.line(surface, color, (x, y + 16), (x - 9, y + 28), 3)
        pygame.draw.line(surface, color, (x, y + 16), (x + 9, y + 28), 3)
        if game.has_gold:
            pygame.draw.circle(surface, GOLD, (x + 14, y + 14), 6)

    def _draw_status(self, surface: pygame.Surface, game, *, show_time: bool, muted: bool) -> None:
        if show_time:
            text = "РЕЖИМ ЧАСОВ  •  ВРЕМЯ — ВЕРНУТЬСЯ В ИГРУ"
            color = LCD_SEGMENT
        elif game.is_game_over:
            text = "КОНЕЦ ИГРЫ  •  ПРОБЕЛ — НОВАЯ ИГРА"
            color = BODY_RED_DARK
        elif game.is_caught:
            text = "ОПАСНОСТЬ!  •  ВОДОЛАЗ ПОЙМАН"
            color = BODY_RED_DARK
        elif game.has_gold:
            text = f"КЛАД В МЕШКЕ: {game.gold_in_sack}  •  ВЕРНИТЕСЬ В ЛОДКУ"
            color = GOLD
        else:
            text = "СТРЕЛКИ — ДВИЖЕНИЕ  •  A/B — РЕЖИМ  •  ПРОБЕЛ — СТАРТ"
            color = LCD_SEGMENT
        rendered = self.font_tiny.render(text, True, color)
        surface.blit(rendered, (self.SCREEN_RECT.centerx - rendered.get_width() // 2, self.SCREEN_RECT.bottom - 18))
        sound = self.font_tiny.render("ЗВУК: ВЫКЛ" if muted else "ЗВУК: ВКЛ", True, LCD_SEGMENT)
        surface.blit(sound, self._screen_point(self.SCREEN_RECT.width - 83, 12))

    def _draw_controls(self, surface: pygame.Surface, mode: str, *, show_time: bool) -> None:
        # Геометрические стрелки вместо символов шрифта — одинаковый вид на всех ПК.
        for name in ("left", "right"):
            rect = self.button_rects[name]
            pygame.draw.circle(surface, BODY_RED_DARK, rect.center, rect.width // 2 + 3)
            pygame.draw.circle(surface, BODY_RED_LIGHT, rect.center, rect.width // 2)
            pygame.draw.circle(surface, BODY_CREAM, rect.center, rect.width // 2 - 8)
            if name == "left":
                points = [(rect.centerx - 23, rect.centery), (rect.centerx + 12, rect.centery - 14), (rect.centerx + 12, rect.centery + 14)]
            else:
                points = [(rect.centerx + 23, rect.centery), (rect.centerx - 12, rect.centery - 14), (rect.centerx - 12, rect.centery + 14)]
            pygame.draw.polygon(surface, INK, points)

        labels = {"mode_a": "ИГРА А", "mode_b": "ИГРА Б", "time": "ВРЕМЯ"}
        for name in ("mode_a", "mode_b", "time"):
            rect = self.button_rects[name]
            pygame.draw.ellipse(surface, BODY_RED_DARK, rect.inflate(4, 4))
            pygame.draw.ellipse(surface, BODY_RED_LIGHT, rect)
            pygame.draw.ellipse(surface, BODY_CREAM, rect.inflate(-8, -8))
            text = labels[name]
            color = BODY_RED_DARK if (name == "mode_a" and mode == MODE_A) or (name == "mode_b" and mode == MODE_B) else INK
            label = self.font_small.render(text, True, color)
            surface.blit(label, (rect.right + 8, rect.centery - label.get_height() // 2))

        # Небольшие пиктограммы звука/будильника справа от кнопок.
        for y, kind in ((119, "sound"), (188, "alarm"), (257, "clock")):
            icon_x = 974
            pygame.draw.circle(surface, INK, (icon_x, y), 5)
            if kind == "sound":
                pygame.draw.arc(surface, INK, (icon_x + 7, y - 7, 13, 14), -0.8, 0.8, 2)
            elif kind == "alarm":
                pygame.draw.line(surface, INK, (icon_x, y - 10), (icon_x, y + 10), 2)
                pygame.draw.line(surface, INK, (icon_x - 7, y), (icon_x + 7, y), 2)
            else:
                pygame.draw.circle(surface, INK, (icon_x, y), 10, width=2)
                pygame.draw.line(surface, INK, (icon_x, y), (icon_x, y - 6), 2)

        # Маленькие подписи режимов внутри LCD, как на оригинальном индикаторе.
        marker = self.font_tiny.render("ИГРА А" if mode == MODE_A else "ИГРА Б", True, LCD_SEGMENT)
        surface.blit(marker, self._screen_point(8, self.SCREEN_RECT.height - 28))
        if show_time:
            clock_marker = self.font_tiny.render("ЧАСЫ", True, LCD_SEGMENT)
            surface.blit(clock_marker, self._screen_point(62, self.SCREEN_RECT.height - 28))

