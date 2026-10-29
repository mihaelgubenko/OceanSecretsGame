# -*- coding: utf-8 -*-
"""Автоматические проверки базовых правил «Тайн океана»."""

import unittest

from game_logic import (
    GameLogic,
    MODE_A,
    MODE_B,
    POS_BOAT,
    POS_CHEST,
    POS_RETURN,
    TENTACLE_MAX_STAGE,
)


class GameLogicTests(unittest.TestCase):
    def test_route_scooping_and_delivery_bonus(self):
        game = GameLogic()

        self.assertTrue(game.move_right())
        self.assertTrue(game.move_right())
        self.assertTrue(game.move_right())
        self.assertEqual(game.diver_pos, POS_CHEST)
        self.assertEqual(game.score, 1)
        self.assertTrue(game.has_gold)

        game.move_right()
        self.assertEqual(game.score, 2)
        self.assertEqual(game.gold_in_sack, 2)

        game.move_left()
        self.assertEqual(game.diver_pos, POS_RETURN)
        game.move_left()
        self.assertEqual(game.diver_pos, POS_BOAT)
        self.assertEqual(game.score, 5)
        self.assertFalse(game.has_gold)
        self.assertEqual(game.gold_in_sack, 0)

    def test_tactical_retreat_from_intermediate_positions(self):
        game = GameLogic()
        game.move_right()
        game.move_right()
        game.move_left()
        self.assertEqual(game.diver_pos, 1)
        game.move_left()
        self.assertEqual(game.diver_pos, POS_BOAT)
        self.assertFalse(game.move_left())

    def test_collision_consumes_life_and_returns_to_boat(self):
        game = GameLogic()
        game.tentacles[0] = TENTACLE_MAX_STAGE

        game.move_right()
        self.assertTrue(game.is_caught)
        self.assertEqual(game.lives, 2)

        game.update(2.0)
        self.assertFalse(game.is_caught)
        self.assertEqual(game.diver_pos, POS_BOAT)

    def test_game_over_after_three_catches(self):
        game = GameLogic()
        for _ in range(3):
            game.tentacles[0] = TENTACLE_MAX_STAGE
            game.move_right()
            self.assertTrue(game.is_caught or game.is_game_over)
            if not game.is_game_over:
                game.update(2.0)
        self.assertTrue(game.is_game_over)
        self.assertEqual(game.lives, 0)

    def test_life_refill_at_200_and_500(self):
        game = GameLogic()
        game.lives = 1
        game.score = 199
        game.diver_pos = POS_CHEST
        game.move_right()
        self.assertEqual(game.score, 200)
        self.assertEqual(game.lives, 3)
        self.assertTrue(game.bonus_200_awarded)

        game.lives = 1
        game.score = 499
        game.diver_pos = POS_CHEST
        game.move_right()
        self.assertEqual(game.score, 500)
        self.assertEqual(game.lives, 3)
        self.assertTrue(game.bonus_500_awarded)

    def test_modes_have_different_base_speed(self):
        game_a = GameLogic(MODE_A)
        game_b = GameLogic(MODE_B)
        self.assertLess(game_b.tick_interval, game_a.tick_interval)
        game_a.score = 1000
        self.assertGreaterEqual(game_a.tick_interval, 0.16)

    def test_invalid_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            GameLogic("C")

    def test_sound_event_queue_is_consumable(self):
        game = GameLogic()
        game.move_right()
        self.assertEqual(game.consume_sound_events(), ["step"])
        self.assertEqual(game.consume_sound_events(), [])


if __name__ == "__main__":
    unittest.main()

