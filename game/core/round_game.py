import math
import random
from pathlib import Path

import pygame

from game.bots.smart_bot import SmartBot
from game.config import ACCENT, HEIGHT, RED, TITLE, WHITE, WIDTH
from game.core.run_history import add_run_entry, load_best_score, load_run_history
from game.core.rounds import (
    BotCollectibleInfo,
    BotEnemyInfo,
    BotWorldState,
    BotZoneInfo,
    FPS,
    LevelState,
    RoundPhase,
    build_level_briefing,
    build_level_rules,
)
from game.entities.collectibles import Coin, Gemstone, InvincibilityPickup, TrapCoin
from game.entities.enemy import SpeedZone, build_enemy
from game.entities.player import Player
from game.rendering.background import BackgroundRenderer
from game.systems.audio import Audio
from game.systems.ui import draw_button, draw_panel, draw_pause_button, draw_stat_card, draw_text


class Game:
    def __init__(self):
        pygame.init()
        self.width = WIDTH
        self.height = HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.audio = Audio()
        self.bot = SmartBot()
        self.background = BackgroundRenderer()
        self.player = Player(100, 100, 50, 4.6)
        self.storage_root = Path(__file__).resolve().parents[2]
        self.best_score = load_best_score(self.storage_root)
        self.run_history = load_run_history(self.storage_root)
        self.toast_text = ""
        self.toast_timer = 0
        self.paused = False
        self.last_mode = "PLAYING"
        self.show_shortcuts = False
        self.menu_overlay = None
        self.state = "MENU"
        self.menu_selected = 0
        self.transition = None
        self.transition_alpha = 255
        self.next_state = None
        self.ai_action_desc = ""
        self.collectibles = []
        self.gemstone = None
        self.enemies = []
        self.speed_zones = []
        self.pending_enemy_spawns = []
        self.level_rules = build_level_rules(1)
        self.level_state = LevelState(level=1, phase=RoundPhase.INTRO, phase_timer=self.level_rules.intro_frames)
        self.completed_level = 0
        self.run_logged = False
        self.reset_run()

    def reset_run(self):
        self.collectibles = []
        self.gemstone = None
        self.enemies = []
        self.speed_zones = []
        self.pending_enemy_spawns = []
        self.level_rules = build_level_rules(1)
        self.level_state = LevelState(
            level=1,
            phase=RoundPhase.INTRO,
            phase_timer=self.level_rules.intro_frames,
            run_start_ticks=pygame.time.get_ticks(),
            highest_level_reached=1,
        )
        self.completed_level = 0
        self.show_shortcuts = False
        self.menu_overlay = None
        self.paused = False
        self.run_logged = False
        self.prepare_level(1)
        self.ai_action_desc = "Scanning for a safe route"
        if self.audio.music_on:
            self.audio.unpause_music()

    def prepare_level(self, level):
        self.level_rules = build_level_rules(level)
        self.level_state.level = level
        self.level_state.highest_level_reached = max(self.level_state.highest_level_reached, level)
        self.level_state.coins_collected_round = 0
        self.level_state.total_real_coins = 0
        self.level_state.phase = RoundPhase.INTRO
        self.level_state.phase_timer = self.level_rules.intro_frames
        player_start = self.get_player_start_position()
        self.player.reset(position=player_start)
        self.player.grant_invulnerability(self.level_rules.intro_frames)
        self.collectibles = []
        self.gemstone = None
        self.pending_enemy_spawns = list(self.level_rules.reinforcement_schedule)
        self.speed_zones = self._build_speed_zones()
        self._spawn_level_collectibles()
        self._spawn_level_enemies()

    def show_toast(self, text, duration=120):
        self.toast_text = text
        self.toast_timer = max(duration, 0)

    def update_toast(self):
        if self.toast_timer > 0:
            self.toast_timer -= 1
            if self.toast_timer == 0:
                self.toast_text = ""

    def change_master_volume(self, delta):
        self.audio.change_music_volume(delta)
        self.audio.change_sound_volume(delta)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.update()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.transition:
                    return
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_m:
                    self.audio.toggle_music()
                if event.key == pygame.K_n:
                    self.audio.toggle_sound()
                if event.key == pygame.K_RIGHTBRACKET:
                    self.change_master_volume(0.05)
                if event.key == pygame.K_LEFTBRACKET:
                    self.change_master_volume(-0.05)
                if event.key == pygame.K_h and (self.state == "MENU" or self.paused):
                    self.show_shortcuts = not self.show_shortcuts
                    continue
                if self.state == "MENU" and self.menu_overlay and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.menu_overlay = None
                    continue
                if self.show_shortcuts and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
                    self.show_shortcuts = False
                    continue
                if self.state == "MENU":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.menu_selected = (self.menu_selected - 1) % 5
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.menu_selected = (self.menu_selected + 1) % 5
                    elif event.key == pygame.K_RETURN:
                        if self.menu_selected == 0:
                            self.start_transition("PLAYING")
                        elif self.menu_selected == 1:
                            self.start_transition("BOT")
                        elif self.menu_selected == 2:
                            self.show_shortcuts = not self.show_shortcuts
                        elif self.menu_selected == 3:
                            self.menu_overlay = "details"
                        elif self.menu_selected == 4:
                            self.menu_overlay = "history"
                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_ESCAPE:
                        self.start_transition("MENU")
                elif event.key == pygame.K_ESCAPE:
                    if self.show_shortcuts:
                        self.show_shortcuts = False
                    elif self.paused:
                        self.paused = False
                        self.audio.unpause_music()
                    else:
                        self.running = False
                if self.state in {"PLAYING", "BOT"}:
                    if event.key == pygame.K_p and self.level_state.phase not in {RoundPhase.INTRO, RoundPhase.LEVEL_COMPLETE}:
                        self.paused = not self.paused
                        self.show_shortcuts = False
                        if self.paused:
                            self.audio.pause_music()
                        else:
                            self.audio.unpause_music()
                    if event.key == pygame.K_c:
                        self.paused = False
                        self.show_shortcuts = False
                        self.audio.unpause_music()
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN and self.state in {"PLAYING", "BOT"} and not self.transition:
                self._handle_game_click(*pygame.mouse.get_pos())
            elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "MENU" and not self.transition:
                self._handle_menu_click(*pygame.mouse.get_pos())
            elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "GAME_OVER" and not self.transition:
                self._handle_game_over_click(*pygame.mouse.get_pos())

    def _handle_game_click(self, mx, my):
        if self.show_shortcuts:
            if self.get_shortcuts_overlay_rects()["close"].collidepoint(mx, my):
                self.show_shortcuts = False
            return
        pause_rect = self.get_pause_button_rect()
        overlay_rects = self.get_pause_overlay_rects()
        if pause_rect.collidepoint(mx, my):
            if self.level_state.phase not in {RoundPhase.INTRO, RoundPhase.LEVEL_COMPLETE}:
                self.paused = not self.paused
                if self.paused:
                    self.audio.pause_music()
                else:
                    self.audio.unpause_music()
        elif self.paused:
            if overlay_rects["resume"].collidepoint(mx, my):
                self.paused = False
                self.audio.unpause_music()
            elif overlay_rects["restart"].collidepoint(mx, my):
                self.start_transition(self.last_mode)
            elif overlay_rects["menu"].collidepoint(mx, my):
                self.start_transition("MENU")
            elif overlay_rects["shortcuts"].collidepoint(mx, my):
                self.show_shortcuts = True
            elif overlay_rects["music"].collidepoint(mx, my):
                self.audio.toggle_music()
            elif overlay_rects["sound"].collidepoint(mx, my):
                self.audio.toggle_sound()

    def _handle_menu_click(self, mx, my):
        if self.show_shortcuts:
            if self.get_shortcuts_overlay_rects()["close"].collidepoint(mx, my):
                self.show_shortcuts = False
            return
        if self.menu_overlay:
            if self.get_menu_overlay_rects()["close"].collidepoint(mx, my):
                self.menu_overlay = None
            return
        rects = self.get_menu_rects()
        if rects["play"].collidepoint(mx, my):
            self.menu_selected = 0
            self.start_transition("PLAYING")
        elif rects["bot"].collidepoint(mx, my):
            self.menu_selected = 1
            self.start_transition("BOT")
        elif rects["shortcuts"].collidepoint(mx, my):
            self.menu_selected = 2
            self.show_shortcuts = True
        elif rects["details_link"].collidepoint(mx, my):
            self.menu_selected = 3
            self.menu_overlay = "details"
        elif rects["history_link"].collidepoint(mx, my):
            self.menu_selected = 4
            self.menu_overlay = "history"
        elif rects["music"].collidepoint(mx, my):
            self.audio.toggle_music()
        elif rects["sound"].collidepoint(mx, my):
            self.audio.toggle_sound()

    def _handle_game_over_click(self, mx, my):
        rects = self.get_game_over_rects()
        if rects["menu"].collidepoint(mx, my):
            self.start_transition("MENU")
        elif rects["restart"].collidepoint(mx, my):
            self.start_transition(self.last_mode)

    def start_transition(self, next_state):
        self.show_shortcuts = False
        self.menu_overlay = None
        if next_state in {"PLAYING", "BOT"}:
            self.last_mode = next_state
            self.paused = False
            if self.audio.music_on:
                self.audio.unpause_music()
        if next_state == "GAME_OVER":
            self.finalize_run("DEFEAT")
            self.audio.play_gameover()
            self.audio.pause_music()
        self.transition = "fadeout"
        self.transition_alpha = 0
        self.next_state = next_state

    def finalize_run(self, outcome):
        if self.run_logged:
            return
        self.level_state.run_outcome = outcome
        duration_seconds = 0
        if self.level_state.run_start_ticks:
            duration_seconds = max(0, (pygame.time.get_ticks() - self.level_state.run_start_ticks) // 1000)
        if self.level_state.points > 0 or self.level_state.highest_level_reached > 1 or self.level_state.gemstones_collected > 0:
            self.run_history = add_run_entry(
                self.storage_root,
                points=self.level_state.points,
                mode=self.last_mode,
                highest_level=self.level_state.highest_level_reached,
                coins_collected=self.level_state.coins_collected_round_total,
                gemstones_collected=self.level_state.gemstones_collected,
                duration_seconds=duration_seconds,
                outcome=outcome,
            )
            self.best_score = self.run_history[0].points if self.run_history else 0
        self.run_logged = True

    def update(self):
        self.update_toast()
        if self.transition:
            self._update_transition()
            return
        if self.state in {"PLAYING", "BOT"} and self.paused:
            return
        if self.state == "PLAYING":
            self._update_play_loop(bot_control=False)
        elif self.state == "BOT":
            self._update_play_loop(bot_control=True)

    def _update_play_loop(self, bot_control):
        if self.level_state.phase == RoundPhase.LEVEL_COMPLETE:
            next_level = self.level_state.level + 1
            self.prepare_level(next_level)
            return

        self._update_collectibles()
        player_speed_scale = self.zone_multiplier_for_rect(self.player.rect)
        magnetic_force = self.compute_magnetic_force()
        wraparound = self.level_rules.mechanics.wraparound
        if bot_control:
            dx, dy = self.bot.choose_move(self.player, self.build_bot_world())
            self.player.apply_bot_control(
                dx,
                dy,
                self.width,
                self.height,
                wraparound=wraparound,
                speed_scale=player_speed_scale,
                external_force=magnetic_force,
            )
            self.ai_action_desc = self.bot.last_description
        else:
            self.player.update(
                self.width,
                self.height,
                wraparound=wraparound,
                speed_scale=player_speed_scale,
                external_force=magnetic_force,
            )
        if self.level_state.phase == RoundPhase.INTRO:
            self.resolve_collectible_collisions()
            self.level_state.phase_timer -= 1
            if self.level_state.phase_timer <= 0:
                self.level_state.phase = RoundPhase.ACTIVE
                self.level_state.phase_timer = self.level_rules.active_frames
            return
        self._update_enemy_reinforcements()
        enemy_targets = self._active_collectibles_for_enemies()
        for enemy in self.enemies:
            enemy.update(self.player, enemy_targets, (self.width, self.height), wraparound, self.speed_zones, self.enemies, self.level_rules)
        self.resolve_enemy_collisions()
        self.resolve_collectible_collisions()
        if not self.player.is_invulnerable:
            for enemy in self.enemies:
                if self.player.rect.colliderect(enemy.rect):
                    self.start_transition("GAME_OVER")
                    return
        self.level_state.phase_timer -= 1
        if self.level_state.phase == RoundPhase.ACTIVE:
            if self.level_state.coins_collected_round >= self.level_state.total_real_coins or self.level_state.phase_timer <= 0:
                self.start_gemstone_phase()
        elif self.level_state.phase == RoundPhase.GEMSTONE:
            if self.level_state.phase_timer <= 0 or self.gemstone is None or not self.gemstone.active:
                self.start_level_complete_phase()

    def _update_collectibles(self):
        for collectible in self.collectibles:
            collectible.update()
        if self.gemstone is not None:
            self.gemstone.update()
            if not self.gemstone.active:
                self.gemstone = None

    def _update_enemy_reinforcements(self):
        if self.level_state.phase != RoundPhase.ACTIVE or not self.pending_enemy_spawns:
            return
        next_spawns = []
        for frames_remaining, kind in self.pending_enemy_spawns:
            frames_remaining -= 1
            if frames_remaining <= 0 and len(self.enemies) < self.level_rules.enemy_cap:
                self._spawn_enemy(kind)
            else:
                next_spawns.append((frames_remaining, kind))
        self.pending_enemy_spawns = next_spawns

    def start_gemstone_phase(self):
        self.collectibles = []
        self.pending_enemy_spawns = []
        self.gemstone = Gemstone(self.level_state.level, self.level_rules.gemstone_frames)
        blocked = [self.player.rect, *[enemy.rect for enemy in self.enemies], *[zone.rect for zone in self.speed_zones]]
        self.gemstone.spawn((self.width, self.height), blocked_rects=blocked, rng=random)
        self.level_state.phase = RoundPhase.GEMSTONE
        self.level_state.phase_timer = self.level_rules.gemstone_frames
        self.show_toast("Gemstone Rush!", duration=90)

    def start_level_complete_phase(self):
        self.gemstone = None
        self.completed_level = self.level_state.level
        self.level_state.phase = RoundPhase.LEVEL_COMPLETE
        self.level_state.phase_timer = 0
        self.player.clear_status_effects()

    def resolve_collectible_collisions(self):
        remaining = []
        for collectible in self.collectibles:
            if not collectible.active:
                continue
            if self.player.rect.colliderect(collectible.rect):
                collectible.active = False
                if isinstance(collectible, TrapCoin):
                    self.player.apply_slow(self.level_rules.trap_slow_frames, self.level_rules.trap_slow_factor)
                    self.show_toast("Trap coin! Movement slowed", duration=100)
                elif isinstance(collectible, InvincibilityPickup):
                    self.player.grant_invulnerability(10 * FPS)
                    self.audio.play_coin()
                    self.show_toast("Invulnerable for 10s", duration=110)
                else:
                    self.level_state.points += collectible.point_value(self.level_state.level)
                    self.level_state.coins_collected_round += 1
                    self.level_state.coins_collected_round_total += 1
                    self.audio.play_coin()
            else:
                remaining.append(collectible)
        self.collectibles = remaining
        if self.gemstone is not None and self.player.rect.colliderect(self.gemstone.rect):
            self.level_state.points += self.gemstone.point_value(self.level_state.level)
            self.level_state.gemstones_collected += 1
            self.audio.play_coin()
            self.show_toast(f"Gemstone +{self.gemstone.point_value(self.level_state.level)}", duration=110)
            self.gemstone.active = False
            self.start_level_complete_phase()

    def resolve_enemy_collisions(self):
        for _ in range(2):
            for index, first in enumerate(self.enemies):
                for second in self.enemies[index + 1:]:
                    if not first.rect.colliderect(second.rect):
                        continue
                    dx = first.rect.centerx - second.rect.centerx
                    dy = first.rect.centery - second.rect.centery
                    if dx == 0 and dy == 0:
                        dx, dy = random.choice((-1, 1)), random.choice((-1, 1))
                    distance = math.hypot(dx, dy)
                    if distance == 0:
                        continue
                    overlap = (first.rect.width / 2 + second.rect.width / 2) - distance
                    if overlap <= 0:
                        continue
                    push_x = (dx / distance) * (overlap / 2 + 1)
                    push_y = (dy / distance) * (overlap / 2 + 1)
                    first.position.x += push_x
                    first.position.y += push_y
                    second.position.x -= push_x
                    second.position.y -= push_y
                    first.sync_rect()
                    second.sync_rect()

    def compute_magnetic_force(self):
        if not self.level_rules.mechanics.magnetic_coins:
            return pygame.Vector2()
        total_force = pygame.Vector2()
        for collectible in self.collectibles:
            if isinstance(collectible, Coin) and collectible.is_real_coin:
                total_force += collectible.magnetic_force(self.player.rect)
        return total_force

    def zone_multiplier_for_rect(self, rect):
        for zone in self.speed_zones:
            if zone.rect.collidepoint(rect.center):
                return zone.multiplier
        return 1.0

    def build_bot_world(self):
        collectibles = [
            BotCollectibleInfo(
                c.kind,
                c.center,
                c.dangerous,
                c.point_value(self.level_state.level),
                getattr(c, "magnetism", 0.0),
            )
            for c in self.collectibles
            if c.active
        ]
        if self.gemstone is not None and self.gemstone.active:
            collectibles.append(
                BotCollectibleInfo(self.gemstone.kind, self.gemstone.center, False, self.gemstone.point_value(self.level_state.level), 0.0)
            )
        enemies = tuple(BotEnemyInfo(enemy.kind, enemy.rect.center) for enemy in self.enemies)
        zones = tuple(BotZoneInfo((zone.rect.x, zone.rect.y, zone.rect.w, zone.rect.h), zone.multiplier) for zone in self.speed_zones)
        pending = tuple(frames for frames, _ in self.pending_enemy_spawns)
        return BotWorldState(
            self.level_state.phase,
            (self.width, self.height),
            self.level_rules.mechanics.wraparound,
            self.level_state.level,
            self.level_state.phase_timer,
            self.player.invulnerable_frames,
            pending,
            tuple(collectibles),
            enemies,
            zones,
        )

    def _active_collectibles_for_enemies(self):
        targets = [collectible for collectible in self.collectibles if collectible.active and collectible.kind != "invincibility"]
        if self.gemstone is not None and self.gemstone.active:
            targets.append(self.gemstone)
        return targets

    def _build_speed_zones(self):
        if not self.level_rules.mechanics.speed_zones:
            return []
        zones = []
        blocked = [pygame.Rect(*self.get_player_start_position(), self.player.rect.width, self.player.rect.height)]
        for index in range(self.level_rules.zone_count):
            rect = self._random_rect(150, 100, blocked, padding=28)
            zone = SpeedZone(rect, 1.28 if index % 2 == 0 else 0.72, "BOOST" if index % 2 == 0 else "SLOW")
            zones.append(zone)
            blocked.append(rect)
        return zones

    def _spawn_level_collectibles(self):
        start_rect = pygame.Rect(*self.get_player_start_position(), self.player.rect.width, self.player.rect.height)
        blocked = [start_rect, *[zone.rect for zone in self.speed_zones]]
        trap_count = int(round(self.level_rules.coin_count * self.level_rules.trap_coin_ratio))
        real_coin_count = max(1, self.level_rules.coin_count - trap_count)
        magnetic_count = int(round(real_coin_count * self.level_rules.magnetic_coin_ratio))
        for index in range(real_coin_count):
            coin = Coin(size=28, magnetism=random.choice((-1.0, 1.0)) if index < magnetic_count else 0.0)
            coin.spawn((self.width, self.height), blocked_rects=blocked, rng=random)
            blocked.append(coin.rect)
            self.collectibles.append(coin)
        for _ in range(trap_count):
            trap = TrapCoin(size=28)
            trap.spawn((self.width, self.height), blocked_rects=blocked, rng=random)
            blocked.append(trap.rect)
            self.collectibles.append(trap)
        if self.level_rules.mechanics.invincibility_pickup and random.random() < self.level_rules.invincibility_spawn_chance:
            pickup = InvincibilityPickup(duration_frames=10 * FPS, size=30)
            pickup.spawn((self.width, self.height), blocked_rects=blocked, rng=random)
            self.collectibles.append(pickup)
        self.level_state.total_real_coins = sum(1 for collectible in self.collectibles if collectible.is_real_coin)

    def _spawn_level_enemies(self):
        self.enemies = []
        for index in range(self.level_rules.enemy_count):
            kind = self.level_rules.enemy_classes[min(index, len(self.level_rules.enemy_classes) - 1)]
            self._spawn_enemy(kind)

    def _spawn_enemy(self, kind):
        size = 28 if kind == "warden" else 24
        x, y = self._spawn_enemy_position(size)
        self.enemies.append(build_enemy(kind, x, y, size))

    def _spawn_enemy_position(self, size):
        margin = size + 36
        best, best_score = None, float("-inf")
        player_center = self.player.rect.center
        exclusion_radius = max(160, min(self.width, self.height) * 0.28)
        for _ in range(36):
            side = random.choice(("top", "right", "bottom", "left"))
            if side == "top":
                x, y = random.randint(0, max(0, self.width - size)), -margin
            elif side == "right":
                x, y = self.width + margin, random.randint(0, max(0, self.height - size))
            elif side == "bottom":
                x, y = random.randint(0, max(0, self.width - size)), self.height + margin
            else:
                x, y = -margin, random.randint(0, max(0, self.height - size))
            center = (x + size / 2.0, y + size / 2.0)
            player_distance = math.dist(center, player_center)
            if player_distance < exclusion_radius:
                continue
            score = player_distance + sum(math.dist(center, enemy.rect.center) * 0.9 for enemy in self.enemies)
            if score > best_score:
                best_score, best = score, (x, y)
        if best is not None:
            return best
        return (-margin, self.height // 2)

    def _random_rect(self, rect_width, rect_height, blocked, padding=18, attempts=50):
        for _ in range(attempts):
            x = random.randint(padding, max(padding, self.width - rect_width - padding))
            y = random.randint(padding, max(padding, self.height - rect_height - padding))
            rect = pygame.Rect(x, y, rect_width, rect_height)
            if any(rect.colliderect(other.inflate(padding, padding)) for other in blocked):
                continue
            return rect
        return pygame.Rect(self.width // 2 - rect_width // 2, self.height // 2 - rect_height // 2, rect_width, rect_height)

    def _update_transition(self):
        if self.transition == "fadeout":
            self.transition_alpha += 16
            if self.transition_alpha >= 255:
                self.transition_alpha = 255
                self.state = self.next_state
                if self.state in {"PLAYING", "BOT", "MENU"}:
                    self.reset_run()
                    self.run_history = load_run_history(self.storage_root)
                    self.best_score = load_best_score(self.storage_root)
                self.transition = "fadein"
        elif self.transition == "fadein":
            self.transition_alpha -= 16
            if self.transition_alpha <= 0:
                self.transition_alpha = 0
                self.transition = None

    def draw(self):
        self.background.draw(self.screen)
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "PLAYING":
            self.draw_game(show_bot_hint=False)
        elif self.state == "BOT":
            self.draw_game(show_bot_hint=True)
        elif self.state == "GAME_OVER":
            self.draw_game_over()
        if self.toast_text:
            draw_text(self.screen, self.toast_text, 22, WHITE, self.width // 2, self.height - 90, center=True, shadow=False)
        if self.transition:
            fade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fade.fill((0, 0, 0, min(self.transition_alpha, 255)))
            self.screen.blit(fade, (0, 0))

    def draw_menu(self):
        mouse_pos = pygame.mouse.get_pos()
        rects = self.get_menu_rects()
        draw_text(self.screen, "Cellrate", 62, WHITE, self.width // 2, 94, center=True, bold=True)
        draw_text(self.screen, f"Best Run : {self.best_score}", 24, ACCENT, self.width // 2, 136, center=True, bold=True, shadow=False)
        draw_text(self.screen, "Arcade harvest. Tactical escape. One enemy at a time.", 18, WHITE, self.width // 2, 168, center=True, shadow=False)
        draw_button(self.screen, "Play", rects["play"].x, rects["play"].y, rects["play"].w, rects["play"].h, active=(self.menu_selected == 0 or rects["play"].collidepoint(mouse_pos)))
        draw_button(self.screen, "BOT", rects["bot"].x, rects["bot"].y, rects["bot"].w, rects["bot"].h, active=(self.menu_selected == 1 or rects["bot"].collidepoint(mouse_pos)))
        draw_button(self.screen, "Shortcuts", rects["shortcuts"].x, rects["shortcuts"].y, rects["shortcuts"].w, rects["shortcuts"].h, active=(self.menu_selected == 2 or rects["shortcuts"].collidepoint(mouse_pos) or self.show_shortcuts), font_size=24, muted=True)
        self.draw_menu_link("Scoring & Levels", rects["details_link"], active=(self.menu_selected == 3 or rects["details_link"].collidepoint(mouse_pos) or self.menu_overlay == "details"), align="left")
        self.draw_menu_link("Top Scores", rects["history_link"], active=(self.menu_selected == 4 or rects["history_link"].collidepoint(mouse_pos) or self.menu_overlay == "history"), align="right")
        self.draw_menu_audio_controls(rects)
        if self.show_shortcuts:
            self.draw_shortcuts_overlay()
        elif self.menu_overlay == "details":
            self.draw_menu_details_overlay()
        elif self.menu_overlay == "history":
            self.draw_run_history_overlay()

    def draw_menu_details_overlay(self):
        rects = self.get_menu_overlay_rects()
        draw_panel(self.screen, rects["panel"])
        draw_text(self.screen, "Scoring & Levels", 30, WHITE, rects["panel"].centerx, rects["panel"].y + 34, center=True, bold=True, shadow=False)
        draw_text(self.screen, "Coins are worth the current level number. Gemstones give 10 + 5 per level.", 18, WHITE, rects["panel"].x + 36, rects["panel"].y + 78, center=False, shadow=False)
        y = rects["panel"].y + 126
        for level in range(1, 6):
            blurb = build_level_briefing(level)
            mechanic = blurb[0] if blurb else "Pure speed and pressure increase."
            draw_text(self.screen, f"Level {level}", 20, ACCENT if level == 1 else WHITE, rects["panel"].x + 40, y, center=False, bold=True, shadow=False)
            draw_text(self.screen, mechanic, 17, WHITE, rects["panel"].x + 152, y + 1, center=False, shadow=False)
            y += 42
        draw_button(self.screen, "Close", rects["close"].x, rects["close"].y, rects["close"].w, rects["close"].h, active=True, font_size=22)

    def draw_run_history_overlay(self):
        rects = self.get_menu_overlay_rects()
        draw_panel(self.screen, rects["panel"])
        panel = rects["panel"]
        draw_text(self.screen, "Top Scores", 30, WHITE, panel.centerx, panel.y + 34, center=True, bold=True, shadow=False)
        draw_text(self.screen, "Rank   Pts   Mode   Lvl   Coins   Gems   Time", 18, ACCENT, panel.x + 42, panel.y + 84, center=False, bold=True, shadow=False)
        if not self.run_history:
            draw_text(self.screen, "No completed runs yet.", 18, WHITE, panel.x + 42, panel.y + 128, center=False, shadow=False)
            draw_button(self.screen, "Close", rects["close"].x, rects["close"].y, rects["close"].w, rects["close"].h, active=True, font_size=22)
            return
        y = panel.y + 126
        for index, entry in enumerate(self.run_history[:10], start=1):
            shade = ACCENT if index == 1 else WHITE
            draw_text(
                self.screen,
                f"{index:>2}    {entry.points:>4}   {entry.mode[:3]:<4}   {entry.highest_level:>2}   {entry.coins_collected:>5}   {entry.gemstones_collected:>4}   {entry.duration_seconds:>4}s",
                18,
                shade,
                panel.x + 42,
                y,
                center=False,
                bold=index == 1,
                shadow=False,
            )
            y += 32
        draw_button(self.screen, "Close", rects["close"].x, rects["close"].y, rects["close"].w, rects["close"].h, active=True, font_size=22)

    def get_pause_button_rect(self):
        return pygame.Rect(18, 18, 44, 44)

    def get_pause_overlay_rects(self):
        panel = pygame.Rect(self.width // 2 - 220, self.height // 2 - 152, 440, 314)
        return {
            "panel": panel,
            "resume": pygame.Rect(panel.x + 90, panel.y + 28, 260, 54),
            "restart": pygame.Rect(panel.x + 30, panel.y + 98, 180, 50),
            "menu": pygame.Rect(panel.x + 230, panel.y + 98, 180, 50),
            "shortcuts": pygame.Rect(panel.x + 30, panel.y + 158, 380, 46),
            "music": pygame.Rect(panel.x + 30, panel.y + 220, 180, 42),
            "sound": pygame.Rect(panel.x + 230, panel.y + 220, 180, 42),
        }

    def get_menu_rects(self):
        btn_w, btn_h = 280, 54
        btn_x = self.width // 2 - btn_w // 2
        top_y = 216
        return {
            "play": pygame.Rect(btn_x, top_y, btn_w, btn_h),
            "bot": pygame.Rect(btn_x, top_y + 70, btn_w, btn_h),
            "shortcuts": pygame.Rect(btn_x, top_y + 140, btn_w, btn_h),
            "details_link": pygame.Rect(28, 26, 210, 30),
            "history_link": pygame.Rect(self.width - 188, 26, 160, 30),
            "music": pygame.Rect(btn_x, top_y + 350, 132, 46),
            "sound": pygame.Rect(btn_x + btn_w - 132, top_y + 350, 132, 46),
        }

    def get_menu_overlay_rects(self):
        panel = pygame.Rect(self.width // 2 - 330, self.height // 2 - 200, 660, 400)
        return {"panel": panel, "close": pygame.Rect(panel.centerx - 90, panel.bottom - 58, 180, 42)}

    def get_game_over_rects(self):
        return {
            "menu": pygame.Rect(self.width // 2 - 190, self.height // 2 + 65, 170, 58),
            "restart": pygame.Rect(self.width // 2 + 20, self.height // 2 + 65, 170, 58),
        }

    def get_shortcuts_overlay_rects(self):
        panel = pygame.Rect(self.width // 2 - 240, self.height // 2 - 176, 480, 352)
        return {"panel": panel, "close": pygame.Rect(panel.x + 135, panel.y + panel.height - 62, 210, 44)}

    def draw_menu_audio_controls(self, rects):
        draw_button(self.screen, "Music", rects["music"].x, rects["music"].y, rects["music"].w, rects["music"].h, active=self.audio.music_on, font_size=22)
        draw_button(self.screen, "Sound", rects["sound"].x, rects["sound"].y, rects["sound"].w, rects["sound"].h, active=self.audio.sound_on, font_size=22)

    def draw_menu_link(self, text, rect, active=False, align="left"):
        color = ACCENT if active else WHITE
        draw_text(self.screen, text, 22, color, rect.x, rect.y, center=False, bold=True, shadow=False)
        underline_y = rect.y + 24
        pygame.draw.line(self.screen, color, (rect.x, underline_y), (rect.x + rect.w, underline_y), 2)

    def draw_pause_overlay(self):
        mouse_pos = pygame.mouse.get_pos()
        rects = self.get_pause_overlay_rects()
        draw_panel(self.screen, rects["panel"])
        draw_button(self.screen, "Resume", rects["resume"].x, rects["resume"].y, rects["resume"].w, rects["resume"].h, active=True, font_size=24)
        draw_button(self.screen, "Restart", rects["restart"].x, rects["restart"].y, rects["restart"].w, rects["restart"].h, font_size=24)
        draw_button(self.screen, "Menu", rects["menu"].x, rects["menu"].y, rects["menu"].w, rects["menu"].h, font_size=24)
        draw_button(self.screen, "Shortcuts", rects["shortcuts"].x, rects["shortcuts"].y, rects["shortcuts"].w, rects["shortcuts"].h, active=rects["shortcuts"].collidepoint(mouse_pos) or self.show_shortcuts, font_size=22, muted=True)
        draw_button(self.screen, "Music", rects["music"].x, rects["music"].y, rects["music"].w, rects["music"].h, active=self.audio.music_on, font_size=20)
        draw_button(self.screen, "Sound", rects["sound"].x, rects["sound"].y, rects["sound"].w, rects["sound"].h, active=self.audio.sound_on, font_size=18)

    def draw_shortcuts_overlay(self):
        rects = self.get_shortcuts_overlay_rects()
        draw_panel(self.screen, rects["panel"])
        draw_text(self.screen, "Shortcuts", 34, WHITE, rects["panel"].centerx, rects["panel"].y + 34, center=True, bold=True, shadow=False)
        rows = [
            ("Move", "Arrow keys or WASD"),
            ("Pause", "P"),
            ("Resume", "C or Resume button"),
            ("Open shortcuts", "H"),
            ("Fullscreen", "F11"),
            ("Music toggle", "M"),
            ("Sound toggle", "N"),
            ("Volume", "[ and ]"),
        ]
        line_y = rects["panel"].y + 82
        for label, command in rows:
            draw_text(self.screen, label, 22, WHITE, rects["panel"].x + 54, line_y, center=False, bold=True, shadow=False)
            draw_text(self.screen, command, 22, WHITE, rects["panel"].right - 190, line_y, center=False, shadow=False)
            line_y += 31
        draw_button(self.screen, "Close", rects["close"].x, rects["close"].y, rects["close"].w, rects["close"].h, active=True, font_size=22)

    def draw_game_over(self):
        draw_text(self.screen, "GAME OVER", 68, RED, self.width // 2, self.height // 2 - 90, center=True, bold=True)
        draw_text(self.screen, f"Points {self.level_state.points}", 34, WHITE, self.width // 2, self.height // 2 - 20, center=True, shadow=False)
        draw_text(self.screen, f"Best {self.best_score}", 28, ACCENT, self.width // 2, self.height // 2 + 18, center=True, shadow=False)
        rects = self.get_game_over_rects()
        draw_button(self.screen, "Menu", rects["menu"].x, rects["menu"].y, rects["menu"].w, rects["menu"].h, font_size=24)
        draw_button(self.screen, "Restart", rects["restart"].x, rects["restart"].y, rects["restart"].w, rects["restart"].h, active=True, font_size=24)

    def draw_game(self, show_bot_hint):
        for zone in self.speed_zones:
            zone.draw(self.screen)
        for collectible in self.collectibles:
            collectible.draw(self.screen)
        if self.gemstone is not None:
            self.gemstone.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        self.player.draw(self.screen)
        self.draw_hud()
        if show_bot_hint and self.level_state.phase in {RoundPhase.ACTIVE, RoundPhase.GEMSTONE}:
            draw_text(self.screen, self.ai_action_desc, 24, WHITE, self.width // 2, self.height - 50, center=True, shadow=False)
        if self.level_state.phase == RoundPhase.INTRO:
            self.draw_phase_banner()
        elif self.level_state.phase == RoundPhase.GEMSTONE:
            draw_text(self.screen, "Gemstone Phase", 26, WHITE, self.width // 2, 58, center=True, bold=True, shadow=False)
        if self.paused:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            self.draw_pause_overlay()
            if self.show_shortcuts:
                self.draw_shortcuts_overlay()

    def draw_hud(self):
        card_w, gap, card_h = 180, 10, 54
        total_width = card_w * 5 + gap * 4
        start_x = self.width - total_width - 18
        remaining = max(0, math.ceil(self.level_state.phase_timer / FPS))
        timer_label = "Time" if self.level_state.phase == RoundPhase.ACTIVE else "Gem"
        cards = [
            ("$ Points :", self.level_state.points, ACCENT),
            ("o Coins :", f"{self.level_state.coins_collected_round}/{self.level_state.total_real_coins}", WHITE),
            ("<> Gems :", self.level_state.gemstones_collected, ACCENT),
            ("x Mult :", self.level_state.multiplier, WHITE),
            (f"{timer_label} :", remaining, ACCENT),
        ]
        for index, (title, value, accent) in enumerate(cards):
            rect = pygame.Rect(start_x + index * (card_w + gap), 16, card_w, card_h)
            draw_stat_card(self.screen, rect, title, value, accent=accent, alpha=132, title_size=16, value_size=26, align_left=True)
        draw_pause_button(self.screen, self.get_pause_button_rect(), active=self.paused)

    def draw_phase_banner(self):
        draw_text(self.screen, f"Level {self.level_state.level}", 56, WHITE, self.width // 2, self.height // 2 - 10, center=True, bold=True, shadow=False)

    def get_player_start_position(self):
        return (
            self.width / 2.0 - self.player.rect.width / 2.0,
            self.height / 2.0 - self.player.rect.height / 2.0,
        )

    def is_fullscreen(self):
        return bool(self.screen.get_flags() & pygame.FULLSCREEN)
