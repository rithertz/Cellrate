import math
import random

import pygame

from game.config import YELLOW


class Coin:
    def __init__(self, size):
        self.size = size
        self.rect = pygame.Rect(0, 0, size, size)
        self.color = YELLOW
        self.angle = 0.0

    def spawn(self, width, height):
        self.rect.x = random.randint(0, width - self.size)
        self.rect.y = random.randint(0, height - self.size)

    def update(self):
        self.angle = (self.angle + 2.2) % 360

    def draw(self, screen):
        center = self.rect.center

        glow_surface = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
        glow_center = glow_surface.get_rect().center
        for radius, alpha in ((int(self.size * 0.72), 22), (int(self.size * 0.5), 38)):
            pygame.draw.circle(glow_surface, (*self.color, alpha), glow_center, radius)
        glow_rect = glow_surface.get_rect(center=center)
        screen.blit(glow_surface, glow_rect.topleft)

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
        coin_rect = coin_surface.get_rect(center=center)
        screen.blit(coin_surface, coin_rect.topleft)
