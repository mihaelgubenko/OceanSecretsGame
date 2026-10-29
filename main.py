# -*- coding: utf-8 -*-
"""Точка входа игры «Электроника ИМ-03 — Тайны океана»."""

from __future__ import annotations

import pygame

from game_logic import GameLogic, MODE_A, MODE_B
from clock_state import ClockState
from lcd_renderer import LCDRenderer
from sound_engine import SoundEngine


WINDOW_SIZE = (1000, 650)
FPS = 60


def _play_pending_sounds(game: GameLogic, sound: SoundEngine) -> None:
    """Проиграть события, накопленные логикой между кадрами."""
    for event_name in game.consume_sound_events():
        sound.play(event_name)


def run() -> None:
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Электроника ИМ-03 — Тайны океана")
    clock = pygame.time.Clock()

    game = GameLogic(MODE_A)
    clock_state = ClockState()
    renderer = LCDRenderer(WINDOW_SIZE)
    sound = SoundEngine()
    elapsed = 0.0
    running = True

    try:
        while running:
            dt = min(clock.tick(FPS) / 1000.0, 0.1)
            elapsed += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RIGHT:
                        if not clock_state.active:
                            game.move_right()
                    elif event.key == pygame.K_LEFT:
                        if not clock_state.active:
                            game.move_left()
                    elif event.key == pygame.K_SPACE:
                        game.restart_game(game.mode)
                        clock_state.leave()
                        elapsed = 0.0
                    elif event.key == pygame.K_a:
                        game.restart_game(MODE_A)
                        clock_state.leave()
                        elapsed = 0.0
                    elif event.key == pygame.K_b:
                        game.restart_game(MODE_B)
                        clock_state.leave()
                        elapsed = 0.0
                    elif event.key == pygame.K_t:
                        clock_state.toggle()
                    elif event.key == pygame.K_m:
                        sound.toggle_mute()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    button = renderer.button_at(event.pos)
                    if button == "left":
                        if not clock_state.active:
                            game.move_left()
                    elif button == "right":
                        if not clock_state.active:
                            game.move_right()
                    elif button == "mode_a":
                        game.restart_game(MODE_A)
                        clock_state.leave()
                        elapsed = 0.0
                    elif button == "mode_b":
                        game.restart_game(MODE_B)
                        clock_state.leave()
                        elapsed = 0.0
                    elif button == "time":
                        clock_state.toggle()

            _play_pending_sounds(game, sound)
            game.update(dt)
            _play_pending_sounds(game, sound)

            renderer.draw(
                screen,
                game,
                elapsed=elapsed,
                show_time=clock_state.active,
                clock_info=clock_state.display,
                muted=not sound.enabled or not sound.available,
            )
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    run()

