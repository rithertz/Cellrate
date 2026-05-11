import pygame
import random

pygame.init()


# ---------------- PLAYER ---------------- #
class Player:
    def __init__(self, x, y, size, speed):
        self.rect = pygame.Rect(x, y, size, size)
        self.base_speed = speed
        self.speed = speed
        self.color = (255, 0, 0)

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

    def clamp(self, width, height):
        self.rect.x = max(0, min(self.rect.x, width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, height - self.rect.height))

    def update(self, width, height):
        self.handle_input()
        self.clamp(width, height)

    def increase_speed(self, amount):
        self.speed += amount

    def reset(self):
        self.rect.topleft = (100, 100)
        self.speed = self.base_speed

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


# ---------------- COIN ---------------- #
class Coin:
    def __init__(self, size):
        self.size = size
        self.rect = pygame.Rect(0, 0, size, size)
        self.color = (255, 255, 0)

    def spawn(self, width, height):
        self.rect.x = random.randint(0, width - self.size)
        self.rect.y = random.randint(0, height - self.size)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


# ---------------- ENEMY ---------------- #
class Enemy:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.base_speed = 1
        self.color = (0, 0, 255)

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


# ---------------- GAME ---------------- #
class Game:
    def __init__(self):
        self.fullscreen = False
        self.width, self.height = 800, 600
        self.screen = None
        self.set_display()

        self.clock = pygame.time.Clock()
        self.running = True

        self.font = pygame.font.SysFont(None, 36)

        self.player = Player(100, 100, 50, 5)
        self.coin = Coin(20)
        self.coin.spawn(self.width, self.height)

        self.enemies = []
        self.spawn_enemy()

        self.score = 0
        self.game_over = False

    # -------- DISPLAY -------- #
    def set_display(self):
        if self.fullscreen:
            info = pygame.display.Info()
            self.width, self.height = info.current_w, info.current_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.RESIZABLE
            )

        pygame.display.set_caption("Final Game")

    # -------- MAIN LOOP -------- #
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

            pygame.display.update()
            self.clock.tick(60)

        pygame.quit()

    # -------- EVENTS -------- #
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    self.set_display()

                elif event.key == pygame.K_r and self.game_over:
                    self.reset()

            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height), pygame.RESIZABLE
                    )

    # -------- GAME LOGIC -------- #
    def update(self):
        if self.game_over:
            return

        self.player.update(self.width, self.height)

        # Coin collision
        if self.player.rect.colliderect(self.coin.rect):
            self.score += 1
            self.player.increase_speed(0.3)
            self.coin.spawn(self.width, self.height)

            # Add new enemy every 5 points
            if self.score % 5 == 0:
                self.spawn_enemy()

        # Enemy difficulty scaling
        enemy_speed = min(1 + self.score * 0.1, 6)

        for enemy in self.enemies:
            enemy.update(self.player.rect, enemy_speed)

            if self.player.rect.colliderect(enemy.rect):
                self.game_over = True

    # -------- DRAW -------- #
    def draw(self):
        self.screen.fill((0, 0, 0))

        self.player.draw(self.screen)
        self.coin.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

        if self.game_over:
            text = self.font.render("GAME OVER - Press R", True, (255, 255, 255))
            self.screen.blit(text, (self.width // 3, self.height // 2))

    # -------- HELPERS -------- #
    def spawn_enemy(self):
        x = random.randint(0, self.width - 30)
        y = random.randint(0, self.height - 30)
        self.enemies.append(Enemy(x, y, 30))

    def reset(self):
        self.player.reset()
        self.coin.spawn(self.width, self.height)
        self.enemies = []
        self.spawn_enemy()
        self.score = 0
        self.game_over = False


# -------- ENTRY -------- #
if __name__ == "__main__":
    Game().run()