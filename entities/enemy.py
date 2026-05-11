import pygame
from config import BLUE

class Enemy:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.color = BLUE

    def update(self, player_rect, speed):
        if self.rect.x < player_rect.x:
            self.rect.x += speed
        elif self.rect.x > player_rect.x:
            self.rect.x -= speed

        if self.rect.y < player_rect.y:
            self.rect.y += speed
        elif self.rect.y > player_rect.y:
            self.rect.y -= speed

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)