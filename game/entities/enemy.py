from __future__ import annotations

import math
import random

import pygame

from game.config import ACCENT, BLUE, WHITE


class BaseEnemy:
    kind = "standard"
    color = BLUE
    speed_factor = 1.0

    def __init__(self, x, y, size):
        self.size = size
        self.rect = pygame.Rect(x, y, size, size)
        self.position = pygame.Vector2(float(x), float(y))
        self.velocity = pygame.Vector2(0, 0)
        self.spawn_age = 0
        self.lateral_sign = random.choice((-1.0, 1.0))

    def update(self, player, collectibles, bounds, wraparound, zones, other_enemies, level_rules):
        self.spawn_age += 1

        target = pygame.Vector2(self.get_target(player, collectibles, bounds))
        center = pygame.Vector2(self.rect.center)
        to_target = target - center
        if to_target.length_squared() <= 0.0001:
            return

        desired_direction = to_target.normalize()
        effective_speed = level_rules.base_enemy_speed * self.speed_factor * self.zone_multiplier(zones)
        desired_velocity = desired_direction * effective_speed

        separation = pygame.Vector2()
        for other in other_enemies:
            if other is self:
                continue
            offset = self.position - other.position
            distance = offset.length()
            if distance <= 0.001 or distance >= level_rules.separation_radius:
                continue
            push = 1.0 - distance / level_rules.separation_radius
            separation += offset.normalize() * (push ** 1.3)

        if self.spawn_age <= 50:
            separation *= 1.45

        steer_target = desired_velocity + separation * level_rules.separation_strength
        self.velocity = self.velocity.lerp(steer_target, level_rules.steering_response)
        if self.velocity.length() > effective_speed * 1.18:
            self.velocity.scale_to_length(effective_speed * 1.18)

        self.position += self.velocity
        self._constrain(bounds, wraparound)

    def get_target(self, player, collectibles, bounds):
        return player.rect.center

    def zone_multiplier(self, zones):
        for zone in zones:
            if zone.rect.collidepoint(self.rect.center):
                return zone.multiplier
        return 1.0

    def _constrain(self, bounds, wraparound):
        width, height = bounds
        self.sync_rect()
        if wraparound:
            if self.rect.right < 0:
                self.position.x = width - 1
            elif self.rect.left > width:
                self.position.x = -self.rect.width + 1
            if self.rect.bottom < 0:
                self.position.y = height - 1
            elif self.rect.top > height:
                self.position.y = -self.rect.height + 1
            self.sync_rect()
            return

        if self.position.x < -self.rect.width:
            self.position.x = -self.rect.width
        elif self.position.x > width:
            self.position.x = width
        if self.position.y < -self.rect.height:
            self.position.y = -self.rect.height
        elif self.position.y > height:
            self.position.y = height
        self.sync_rect()

    def sync_rect(self):
        self.rect.x = int(round(self.position.x))
        self.rect.y = int(round(self.position.y))

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=8)


class StandardEnemy(BaseEnemy):
    kind = "standard"
    color = BLUE
    speed_factor = 1.0


class InterceptorEnemy(BaseEnemy):
    kind = "interceptor"
    color = (70, 215, 255)
    speed_factor = 1.08

    def get_target(self, player, collectibles, bounds):
        velocity = pygame.Vector2(player.velocity)
        if velocity.length_squared() <= 0.01:
            return player.rect.center
        lead = velocity.normalize() * min(95.0, 42.0 + velocity.length() * 10.0)
        return pygame.Vector2(player.rect.center) + lead


class WardenEnemy(BaseEnemy):
    kind = "warden"
    color = (160, 205, 255)
    speed_factor = 0.95

    def get_target(self, player, collectibles, bounds):
        player_center = pygame.Vector2(player.rect.center)
        valuable = [collectible for collectible in collectibles if collectible.active and collectible.kind in {"gemstone", "coin"}]
        if not valuable:
            return player_center

        anchor = min(valuable, key=lambda collectible: pygame.Vector2(collectible.center).distance_to(player_center))
        anchor_center = pygame.Vector2(anchor.center)
        route = anchor_center - player_center
        if route.length_squared() <= 0.001:
            return anchor_center
        midpoint = player_center.lerp(anchor_center, 0.58)
        lateral = pygame.Vector2(-route.y, route.x)
        if lateral.length_squared() > 0.001:
            lateral = lateral.normalize() * self.lateral_sign * 26.0
        return midpoint + lateral

    def draw(self, screen):
        super().draw(screen)
        notch = pygame.Rect(self.rect.x + 4, self.rect.y + 4, max(6, self.rect.width - 8), max(6, self.rect.height - 8))
        pygame.draw.rect(screen, WHITE, notch, width=2, border_radius=6)


class SpeedZone:
    def __init__(self, rect, multiplier, label):
        self.rect = rect
        self.multiplier = multiplier
        self.label = label
        self.color = (60, 220, 150, 70) if multiplier > 1.0 else (115, 155, 255, 70)
        self.edge = (80, 255, 180) if multiplier > 1.0 else (150, 200, 255)

    def draw(self, screen):
        surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surface, self.color, surface.get_rect(), border_radius=18)
        pygame.draw.rect(surface, (*self.edge, 220), surface.get_rect(), width=2, border_radius=18)
        screen.blit(surface, self.rect.topleft)


ENEMY_TYPES = {
    "standard": StandardEnemy,
    "interceptor": InterceptorEnemy,
    "warden": WardenEnemy,
}


def build_enemy(enemy_kind, x, y, size):
    enemy_class = ENEMY_TYPES.get(enemy_kind, StandardEnemy)
    return enemy_class(x, y, size)
