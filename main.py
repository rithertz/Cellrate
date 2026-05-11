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

    def clamp_to_screen(self, width, height):
        self.rect.x = max(0, min(self.rect.x, width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, height - self.rect.height))

    def update(self, width, height):
        self.handle_input()
        self.clamp_to_screen(width, height)

    def increase_speed(self, amount):
        self.speed += amount

    def reset(self):
        self.rect.x, self.rect.y = 100, 100
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


# ---------------- GAME ---------------- #
class Game:
    def __init__(self):
        # Display
        self.fullscreen = False
        self.width, self.height = 800, 600
        self.screen = None
        self.set_display()

        # Core
        self.clock = pygame.time.Clock()
        self.running = True

        # Game state
        self.score = 0
        self.game_over = False

        # Font
        self.font = pygame.font.SysFont(None, 36)

        # Objects
        self.player = Player(100, 100, 50, 5)
        self.coin = Coin(20)
        self.coin.spawn(self.width, self.height)

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

        pygame.display.set_caption("OOP Game")

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
                    self.reset_game()

            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height), pygame.RESIZABLE
                    )

    # -------- UPDATE -------- #
    def update(self):
        if self.game_over:
            return

        self.player.update(self.width, self.height)

        # Coin collision
        if self.player.rect.colliderect(self.coin.rect):
            self.score += 1
            self.player.increase_speed(0.3)
            self.coin.spawn(self.width, self.height)

    # -------- DRAW -------- #
    def draw(self):
        self.screen.fill((0, 0, 0))

        self.player.draw(self.screen)
        self.coin.draw(self.screen)

        # Score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

        if self.game_over:
            over_text = self.font.render("GAME OVER - Press R", True, (255, 255, 255))
            self.screen.blit(over_text, (self.width // 3, self.height // 2))

    # -------- RESET -------- #
    def reset_game(self):
        self.score = 0
        self.game_over = False
        self.player.reset()
        self.coin.spawn(self.width, self.height)


# -------- ENTRY -------- #
if __name__ == "__main__":
    game = Game()
    game.run()