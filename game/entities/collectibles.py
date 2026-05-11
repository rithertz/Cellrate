from __future__ import annotations

import math
import random

import pygame

from game.config import ACCENT, RED, WHITE, YELLOW


def spawn_rect(size, bounds, blocked_rects=None, rng=None, padding=18, attempts=80):
    rng = rng or random
    width, height = bounds
    blocked_rects = blocked_rects or []

    for _ in range(attempts):
        x = rng.randint(padding, max(padding, width - size - padding))
        y = rng.randint(padding, max(padding, height - size - padding))
        rect = pygame.Rect(x, y, size, size)
        if any(rect.colliderect(blocked.inflate(padding, padding)) for blocked in blocked_rects):
            continue
        return rect

    return pygame.Rect(max(0, width // 2 - size // 2), max(0, height // 2 - size // 2), size, size)


class BaseCollectible:
    kind = "collectible"
    dangerous = False
    is_real_coin = False

    def __init__(self, size):
        self.size = size
        self.rect = pygame.Rect(0, 0, size, size)
        self.active = True
        self.angle = 0.0

    @property
    def center(self):
        return self.rect.center

    def spawn(self, bounds, blocked_rects=None, rng=None):
        self.rect = spawn_rect(self.size, bounds, blocked_rects=blocked_rects, rng=rng)
        self.active = True

    def update(self):
        self.angle = (self.angle + 2.2) % 360

    def point_value(self, level):
        return 0

    def draw(self, screen):
        raise NotImplementedError


class Coin(BaseCollectible):
    kind = "coin"
    is_real_coin = True

    def __init__(self, size=28, magnetism=0.0):
        super().__init__(size)
        self.color = YELLOW
        self.magnetism = float(magnetism)

    def point_value(self, level):
        return max(1, int(level))

    def magnetic_force(self, player_rect):
        if not self.active or abs(self.magnetism) <= 0.001:
            return pygame.Vector2()

        delta = pygame.Vector2(self.rect.centerx - player_rect.centerx, self.rect.centery - player_rect.centery)
        distance = delta.length()
        if distance <= 0.001 or distance > 220:
            return pygame.Vector2()

        strength = (1.0 - distance / 220.0) * 0.16
        return delta.normalize() * strength * self.magnetism

    def draw(self, screen):
        if not self.active:
            return

        center = self.rect.center
        glow_surface = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
        glow_center = glow_surface.get_rect().center
        for radius, alpha in ((int(self.size * 0.72), 22), (int(self.size * 0.5), 38)):
            pygame.draw.circle(glow_surface, (*self.color, alpha), glow_center, radius)
        screen.blit(glow_surface, glow_surface.get_rect(center=center).topleft)

        coin_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        local_center = coin_surface.get_rect().center
        radius = int(self.size * 0.42)
        points = []
        for index in range(4):
            angle = math.radians(self.angle + 45 + index * 90)
            points.append(
                (
                    local_center[0] + math.cos(angle) * radius,
                    local_center[1] + math.sin(angle) * radius,
                )
            )
        pygame.draw.polygon(coin_surface, self.color, points)
        inner_points = []
        inner_radius = int(radius * 0.66)
        for index in range(4):
            angle = math.radians(self.angle + 45 + index * 90)
            inner_points.append(
                (
                    local_center[0] + math.cos(angle) * inner_radius,
                    local_center[1] + math.sin(angle) * inner_radius,
                )
            )
        pygame.draw.polygon(coin_surface, (255, 243, 188), inner_points)
        pygame.draw.polygon(coin_surface, (255, 236, 150), points, width=2)

        if self.magnetism > 0:
            pygame.draw.circle(coin_surface, (90, 180, 255, 210), local_center, int(radius * 1.2), width=2)
        elif self.magnetism < 0:
            pygame.draw.circle(coin_surface, (255, 110, 150, 210), local_center, int(radius * 1.2), width=2)

        screen.blit(coin_surface, coin_surface.get_rect(center=center).topleft)


class TrapCoin(Coin):
    kind = "trap_coin"
    dangerous = True
    is_real_coin = False

    def __init__(self, size=28):
        super().__init__(size=size, magnetism=0.0)
        self.color = (255, 106, 92)

    def point_value(self, level):
        return 0

    def draw(self, screen):
        super().draw(screen)
        if not self.active:
            return
        pygame.draw.circle(screen, RED, self.rect.center, max(4, self.size // 6), width=2)


class Gemstone(BaseCollectible):
    kind = "gemstone"

    def __init__(self, level, decay_frames, size=34):
        super().__init__(size)
        self.level = level
        self.decay_frames = decay_frames
        self.remaining_frames = decay_frames
        self.hue_tick = 0.0

    def point_value(self, level):
        return 10 + max(0, self.level - 1) * 5

    def spawn(self, bounds, blocked_rects=None, rng=None):
        super().spawn(bounds, blocked_rects=blocked_rects, rng=rng)
        self.remaining_frames = self.decay_frames
        self.hue_tick = 0.0

    def update(self):
        if not self.active:
            return
        self.hue_tick = (self.hue_tick + 0.08) % (math.pi * 2)
        self.remaining_frames -= 1
        if self.remaining_frames <= 0:
            self.active = False

    def decay_ratio(self):
        return max(0.0, min(1.0, self.remaining_frames / max(1, self.decay_frames)))

    def draw(self, screen):
        if not self.active:
            return

        center = self.rect.center
        pulse = 0.75 + math.sin(self.hue_tick * 2.0) * 0.18
        glow_surface = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
        glow_center = glow_surface.get_rect().center
        glow_color = (
            int(145 + 80 * math.sin(self.hue_tick)),
            int(150 + 70 * math.sin(self.hue_tick + 2.1)),
            int(190 + 55 * math.sin(self.hue_tick + 4.2)),
            int(80 * self.decay_ratio() + 40),
        )
        pygame.draw.circle(glow_surface, glow_color, glow_center, int(self.size * pulse))
        screen.blit(glow_surface, glow_surface.get_rect(center=center).topleft)

        gem_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        local_center = gem_surface.get_rect().center
        radii = (0.58, 0.22, 0.58, 0.24, 0.58, 0.22)
        points = []
        for index, scale in enumerate(radii):
            angle = math.radians(self.angle + index * 60 - 90)
            points.append(
                (
                    local_center[0] + math.cos(angle) * self.size * scale,
                    local_center[1] + math.sin(angle) * self.size * scale,
                )
            )
        fill_color = (
            int(190 + 50 * math.sin(self.hue_tick)),
            int(150 + 70 * math.sin(self.hue_tick + 1.6)),
            int(230 + 20 * math.sin(self.hue_tick + 3.2)),
        )
        pygame.draw.polygon(gem_surface, fill_color, points)
        pygame.draw.polygon(gem_surface, WHITE, points, width=2)

        if self.decay_ratio() < 0.45:
            alpha = int((1.0 - self.decay_ratio()) * 150)
            pygame.draw.line(gem_surface, (255, 255, 255, alpha), (local_center[0] - 12, local_center[1] - 12), (local_center[0] + 12, local_center[1] + 12), width=2)

        screen.blit(gem_surface, gem_surface.get_rect(center=center).topleft)


class InvincibilityPickup(BaseCollectible):
    kind = "invincibility"

    def __init__(self, duration_frames, size=30):
        super().__init__(size)
        self.duration_frames = duration_frames

    def draw(self, screen):
        if not self.active:
            return

        center = self.rect.center
        surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        local_center = surface.get_rect().center
        radius = self.size * 0.44
        pygame.draw.circle(surface, (*ACCENT, 90), local_center, int(radius * 1.35))
        pygame.draw.circle(surface, WHITE, local_center, int(radius), width=3)

        star_points = []
        for index in range(8):
            angle = math.radians(self.angle * 2 + index * 45 - 90)
            scale = radius if index % 2 == 0 else radius * 0.45
            star_points.append(
                (
                    local_center[0] + math.cos(angle) * scale,
                    local_center[1] + math.sin(angle) * scale,
                )
            )
        pygame.draw.polygon(surface, (120, 220, 255), star_points)
        screen.blit(surface, surface.get_rect(center=center).topleft)
