import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from game.bots.smart_bot import SmartBot
from game.core.round_game import Game
from game.core.run_history import add_run_entry, load_best_score, load_run_history, reset_best_score
from game.core.rounds import (
    BotCollectibleInfo,
    BotEnemyInfo,
    BotWorldState,
    BotZoneInfo,
    FPS,
    RoundPhase,
    build_level_rules,
    gemstone_bonus_for_level,
)
from game.entities.collectibles import Gemstone, TrapCoin
from game.entities.player import Player


class RoundSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_level_rule_schedule_and_brief_level_one(self):
        level1 = build_level_rules(1)
        level2 = build_level_rules(2)
        level3 = build_level_rules(3)
        level4 = build_level_rules(4)
        level5 = build_level_rules(5)

        self.assertEqual(level1.enemy_cap, 3)
        self.assertEqual(level1.enemy_count, 0)
        self.assertEqual(level1.reinforcement_schedule[0][0], 2)
        self.assertEqual(level2.enemy_count, 0)
        self.assertGreater(len(level2.reinforcement_schedule), 1)
        self.assertGreaterEqual(level3.zone_count, 4)
        self.assertFalse(level1.mechanics.wraparound)
        self.assertTrue(level4.mechanics.magnetic_coins)
        self.assertTrue(level5.mechanics.invincibility_pickup)

    def test_gemstone_bonus_and_decay(self):
        gemstone = Gemstone(level=3, decay_frames=5)
        gemstone.spawn((300, 200), blocked_rects=[], rng=None)

        self.assertEqual(gemstone_bonus_for_level(1), 10)
        self.assertEqual(gemstone.point_value(3), 20)

        for _ in range(5):
            gemstone.update()
        self.assertFalse(gemstone.active)

    def test_player_starts_centered_and_intro_invulnerable(self):
        game = Game()
        game.state = "PLAYING"
        expected_x = game.width / 2.0 - game.player.rect.width / 2.0
        expected_y = game.height / 2.0 - game.player.rect.height / 2.0

        self.assertAlmostEqual(game.player.position.x, expected_x)
        self.assertAlmostEqual(game.player.position.y, expected_y)
        self.assertEqual(game.level_state.phase, RoundPhase.INTRO)
        self.assertGreater(game.player.invulnerable_frames, 0)
        self.assertEqual(len(game.enemies), 0)

        for _ in range(game.level_rules.intro_frames - 1):
            game.update()
        self.assertEqual(game.level_state.phase, RoundPhase.INTRO)
        game.update()
        self.assertEqual(game.level_state.phase, RoundPhase.ACTIVE)
        self.assertEqual(len(game.enemies), 0)

    def test_level_one_reinforcements_arrive_later(self):
        game = Game()
        game.state = "PLAYING"
        self.assertEqual(len(game.enemies), 0)

        game.level_state.phase = RoundPhase.ACTIVE
        game.level_state.phase_timer = game.level_rules.active_frames
        for _ in range(3):
            game._update_enemy_reinforcements()
        self.assertEqual(len(game.enemies), 1)

        for _ in range(6 * FPS + 1):
            game._update_enemy_reinforcements()
        self.assertGreaterEqual(len(game.enemies), 2)

    def test_spawn_points_avoid_player_center(self):
        game = Game()
        game.state = "PLAYING"
        game.level_state.phase = RoundPhase.ACTIVE
        game.level_state.phase_timer = game.level_rules.active_frames
        for _ in range(3):
            game._update_enemy_reinforcements()
        for enemy in game.enemies:
            distance = pygame.Vector2(enemy.rect.center).distance_to(game.player.rect.center)
            self.assertGreaterEqual(distance, 150)

    def test_trap_coin_penalty_awards_no_points(self):
        game = Game()
        trap = TrapCoin(size=28)
        trap.rect.center = game.player.rect.center
        game.collectibles = [trap]
        game.level_state.points = 7
        game.resolve_collectible_collisions()

        self.assertEqual(game.level_state.points, 7)
        self.assertGreater(game.player.slow_frames, 0)

    def test_pause_button_is_top_left(self):
        game = Game()
        rect = game.get_pause_button_rect()
        self.assertEqual(rect.x, 18)
        self.assertEqual(rect.y, 18)

    def test_menu_overlays_open_from_corner_links(self):
        game = Game()
        rects = game.get_menu_rects()
        details_rect = rects["details_link"]
        history_rect = rects["history_link"]
        self.assertLess(details_rect.x, 40)
        self.assertGreater(history_rect.right, game.width - 40)
        game._handle_menu_click(details_rect.centerx, details_rect.centery)
        self.assertEqual(game.menu_overlay, "details")
        game.menu_overlay = None
        game._handle_menu_click(history_rect.centerx, history_rect.centery)
        self.assertEqual(game.menu_overlay, "history")

    def test_run_history_sorting_and_best_score_mirror(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reset_best_score(root)
            for index in range(12):
                add_run_entry(
                    root,
                    points=index * 10,
                    mode="BOT" if index % 2 else "PLAYING",
                    highest_level=1 + index % 5,
                    coins_collected=10 + index,
                    gemstones_collected=index % 3,
                    duration_seconds=30 + index,
                    outcome="DEFEAT",
                )

            entries = load_run_history(root)
            self.assertEqual(len(entries), 10)
            self.assertEqual(entries[0].points, 110)
            self.assertEqual(load_best_score(root), 110)

    def test_bot_prefers_safe_coin_and_wraparound(self):
        bot = SmartBot()
        player = Player(18, 140, 40, 4.6)
        world = BotWorldState(
            phase=RoundPhase.ACTIVE,
            bounds=(400, 300),
            wraparound=True,
            level=2,
            phase_timer=400,
            invulnerability_frames=0,
            pending_reinforcements=(120,),
            collectibles=(BotCollectibleInfo("coin", (392, 140), False, 2),),
            enemies=(BotEnemyInfo("standard", (200, 260)),),
            zones=(BotZoneInfo((40, 100, 100, 80), 0.72),),
        )
        move_x, _ = bot.choose_move(player, world)
        self.assertLessEqual(move_x, 0)

    def test_bot_uses_intro_window_for_coin_setup(self):
        bot = SmartBot()
        player = Player(180, 140, 40, 4.6)
        world = BotWorldState(
            phase=RoundPhase.INTRO,
            bounds=(400, 300),
            wraparound=False,
            level=1,
            phase_timer=120,
            invulnerability_frames=120,
            pending_reinforcements=(2, 360, 720),
            collectibles=(BotCollectibleInfo("coin", (250, 140), False, 1),),
            enemies=(),
            zones=(),
        )
        move_x, move_y = bot.choose_move(player, world)
        self.assertGreaterEqual(move_x, 0)
        self.assertLessEqual(abs(move_y), 1)

    def test_bot_avoids_trap_when_real_coin_exists(self):
        bot = SmartBot()
        player = Player(120, 120, 40, 4.6)
        trap_world = BotWorldState(
            phase=RoundPhase.ACTIVE,
            bounds=(400, 300),
            wraparound=False,
            level=4,
            phase_timer=300,
            invulnerability_frames=0,
            pending_reinforcements=(),
            collectibles=(
                BotCollectibleInfo("trap_coin", (90, 120), True, 0),
                BotCollectibleInfo("coin", (220, 120), False, 4),
            ),
            enemies=(BotEnemyInfo("standard", (350, 260)),),
            zones=(),
        )
        move_x, move_y = bot.choose_move(player, trap_world)
        self.assertGreaterEqual(move_x, 0)
        self.assertEqual(move_y, 0)


if __name__ == "__main__":
    unittest.main()
