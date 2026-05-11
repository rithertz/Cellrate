import pygame
import random

from config import *
from entities.player import Player
from entities.coin import Coin
from entities.enemy import Enemy
from systems.ui import draw_text
from systems.audio import Audio


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Game")

        self.clock = pygame.time.Clock()
        self.running = True

        self.audio = Audio()

        self.player = Player(100, 100, 50, 5)
        self.coin = Coin(20)
        self.coin.spawn(WIDTH, HEIGHT)

        self.enemies = [Enemy(300, 200, 30)]

        self.score = 0
        self.state = "MENU"

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

            pygame.display.update()
            self.clock.tick(60)

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.state = "PLAYING"
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        if self.state != "PLAYING":
            return

        self.player.update(WIDTH, HEIGHT)

        if self.player.rect.colliderect(self.coin.rect):
            self.score += 1
            self.player.increase_speed(0.3)
            self.coin.spawn(WIDTH, HEIGHT)
            self.audio.coin.play()

        for enemy in self.enemies:
            enemy.update(self.player.rect, min(1 + self.score * 0.1, 6))
            if self.player.rect.colliderect(enemy.rect):
                self.audio.gameover.play()
                self.state = "GAME_OVER"

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "MENU":
            draw_text(self.screen, "Press ENTER to Start", 40, WHITE, WIDTH//2, HEIGHT//2)

        elif self.state == "PLAYING":
            self.player.draw(self.screen)
            self.coin.draw(self.screen)
            for e in self.enemies:
                e.draw(self.screen)

            draw_text(self.screen, f"Score: {self.score}", 30, WHITE, 10, 10, False)

        elif self.state == "GAME_OVER":
            draw_text(self.screen, "GAME OVER", 60, WHITE, WIDTH//2, HEIGHT//2)