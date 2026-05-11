import pygame
import random
from config import YELLOW

class Coin:
    def __init__(self, size):
        self.size = size
        self.rect = pygame.Rect(0, 0, size, size)
        self.color = YELLOW

    def spawn(self, width, height):
        self.rect.x = random.randint(0, width - self.size)
        self.rect.y = random.randint(0, height - self.size)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)