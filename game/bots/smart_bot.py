import math

import pygame

from game.core.rounds import BotWorldState, RoundPhase
from game.entities.player import Player


class SmartBot:
    def __init__(self):
        self._last_description = "Surveying the field"

    @property
    def last_description(self):
        return self._last_description

    def choose_move(self, player, world: BotWorldState):
        target = self._select_target(player, world)
        if target is None:
            self._last_description = "Holding pattern"
            return 0, 0

        best_score = float("-inf")
        best_move = (0, 0)

        for move_x, move_y in self._candidate_moves():
            score = self._score_move(player, world, target, move_x, move_y)
            if score > best_score:
                best_score = score
                best_move = (move_x, move_y)

        self._last_description = self._describe_target(world.phase, target.kind)
        return best_move

    def _candidate_moves(self):
        return [
            (0, 0),
            (1, 0),
            (1, 1),
            (0, 1),
            (-1, 1),
            (-1, 0),
            (-1, -1),
            (0, -1),
            (1, -1),
        ]

    def _select_target(self, player, world):
        safe_collectibles = [item for item in world.collectibles if not item.dangerous]
        gemstone = next((item for item in safe_collectibles if item.kind == "gemstone"), None)
        invincibility = next((item for item in safe_collectibles if item.kind == "invincibility"), None)
        real_coins = [item for item in safe_collectibles if item.kind == "coin"]

        nearest_enemy = min(
            (self._distance(player.rect.center, enemy.center, world.wraparound, world.bounds) for enemy in world.enemies),
            default=9999.0,
        )

        if world.phase == RoundPhase.GEMSTONE and gemstone is not None:
            return gemstone
        if world.phase == RoundPhase.INTRO and real_coins:
            return max(real_coins, key=lambda item: self._intro_priority(player, world, item))
        if not player.is_invulnerable and invincibility is not None and nearest_enemy < 150:
            return invincibility
        if real_coins:
            return max(real_coins, key=lambda item: self._coin_priority(player, world, item))
        if gemstone is not None:
            return gemstone
        if invincibility is not None:
            return invincibility
        return min(safe_collectibles, key=lambda item: self._distance(player.rect.center, item.center, world.wraparound, world.bounds), default=None)

    def _score_move(self, player, world, target, move_x, move_y):
        speed_scale = self._zone_multiplier(player.rect.center, world.zones)
        velocity = Player.advance_velocity(
            pygame.Vector2(player.velocity),
            (move_x, move_y),
            8 if (move_x or move_y) else 0,
            player.get_speed_cap(8, speed_scale=speed_scale),
            player.acceleration,
            player.coast_drag,
            player.counter_brake,
        )

        simulated_center = pygame.Vector2(player.rect.center) + velocity
        simulated_center = self._wrap_center(simulated_center, player.rect.size, world.bounds, world.wraparound)

        distance_to_target = self._distance(simulated_center, target.center, world.wraparound, world.bounds)
        nearest_enemy = min(
            (self._distance(simulated_center, enemy.center, world.wraparound, world.bounds) for enemy in world.enemies),
            default=9999.0,
        )
        center_pressure = self._distance(simulated_center, (world.bounds[0] / 2.0, world.bounds[1] / 2.0), world.wraparound, world.bounds)

        score = 0.0
        score -= distance_to_target * 3.0
        score += min(nearest_enemy, 180.0) * 2.8
        if nearest_enemy < 110:
            score += center_pressure * 0.14

        zone_multiplier = self._zone_multiplier(simulated_center, world.zones)
        if zone_multiplier > 1.0:
            score += 24.0
        elif zone_multiplier < 1.0:
            score -= 38.0

        if target.kind == "gemstone":
            score += 260.0
        elif target.kind == "invincibility":
            score += 180.0
        elif target.kind == "coin":
            score += target.value * 28.0
            if world.phase == RoundPhase.INTRO:
                score += 52.0

        if nearest_enemy < 60:
            score -= (60 - nearest_enemy) * 12.0
        if world.pending_reinforcements and min(world.pending_reinforcements) < 150:
            score += self._edge_clearance_bonus(simulated_center, world.bounds)
        if player.is_invulnerable:
            score += 28.0

        return score

    def _describe_target(self, phase, kind):
        if phase == RoundPhase.GEMSTONE and kind == "gemstone":
            return "Dashing for gemstone"
        if kind == "invincibility":
            return "Securing shield"
        if kind == "coin":
            return "Harvesting coins"
        return "Reading the field"

    def _zone_multiplier(self, center, zones):
        point = (int(center[0]), int(center[1]))
        for zone in zones:
            x, y, w, h = zone.rect
            if pygame.Rect(x, y, w, h).collidepoint(point):
                return zone.multiplier
        return 1.0

    def _distance(self, first, second, wraparound, bounds):
        dx = float(first[0]) - float(second[0])
        dy = float(first[1]) - float(second[1])
        if wraparound:
            width, height = bounds
            dx = min(abs(dx), width - abs(dx)) * (1 if dx >= 0 else -1)
            dy = min(abs(dy), height - abs(dy)) * (1 if dy >= 0 else -1)
        return math.hypot(dx, dy)

    def _wrap_center(self, center, size, bounds, wraparound):
        if not wraparound:
            return center
        width, height = bounds
        x, y = center
        half_w = size[0] / 2.0
        half_h = size[1] / 2.0
        if x < -half_w:
            x = width + half_w
        elif x > width + half_w:
            x = -half_w
        if y < -half_h:
            y = height + half_h
        elif y > height + half_h:
            y = -half_h
        return pygame.Vector2(x, y)

    def _coin_priority(self, player, world, item):
        distance = self._distance(player.rect.center, item.center, world.wraparound, world.bounds)
        enemy_penalty = min(
            (
                self._distance(item.center, enemy.center, world.wraparound, world.bounds)
                for enemy in world.enemies
            ),
            default=250.0,
        )
        priority = item.value * 65.0 - distance * 1.8 + enemy_penalty * 1.15
        if world.pending_reinforcements and min(world.pending_reinforcements) < 180:
            priority += self._edge_clearance_bonus(item.center, world.bounds) * 0.8
        if abs(item.magnetism) > 0.001:
            priority -= 18.0
        return priority

    def _edge_clearance_bonus(self, center, bounds):
        x_margin = min(center[0], bounds[0] - center[0])
        y_margin = min(center[1], bounds[1] - center[1])
        return max(0.0, min(x_margin, y_margin) - 70.0)

    def _intro_priority(self, player, world, item):
        distance = self._distance(player.rect.center, item.center, world.wraparound, world.bounds)
        center_distance = self._distance(item.center, (world.bounds[0] / 2.0, world.bounds[1] / 2.0), world.wraparound, world.bounds)
        return item.value * 90.0 - distance * 1.4 + center_distance * 0.2
