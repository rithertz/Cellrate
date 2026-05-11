import pygame
from config import RED

class Player:
    def __init__(self, x, y, size, speed):
        self.rect = pygame.Rect(x, y, size, size)
        self.base_speed = speed
        self.speed = speed
        self.color = RED

    def handle_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed

    def update(self, width, height):
        self.handle_input()
        self.rect.x = max(0, min(self.rect.x, width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, height - self.rect.height))

    def increase_speed(self, amount):
        self.speed += amount

    def reset(self):
        self.rect.topleft = (100, 100)
        self.speed = self.base_speed

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)