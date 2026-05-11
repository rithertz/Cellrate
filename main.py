import pygame

pygame.init()


# ---------------- PLAYER CLASS ---------------- #
class Player:
    def __init__(self, x, y, size, speed):
        self.rect = pygame.Rect(x, y, size, size)
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

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


# ---------------- GAME CLASS ---------------- #
class Game:
    def __init__(self):
        # Display settings
        self.fullscreen = False
        self.width = 800
        self.height = 600

        self.screen = None
        self.set_display()

        # Core systems
        self.clock = pygame.time.Clock()
        self.running = True

        # Game objects
        self.player = Player(100, 100, 50, 5)

    # -------- DISPLAY -------- #
    def set_display(self):
        if self.fullscreen:
            info = pygame.display.Info()
            self.width, self.height = info.current_w, info.current_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.RESIZABLE
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

            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height),
                        pygame.RESIZABLE
                    )

    # -------- UPDATE -------- #
    def update(self):
        self.player.update(self.width, self.height)

    # -------- DRAW -------- #
    def draw(self):
        self.screen.fill((0, 0, 0))
        self.player.draw(self.screen)


# -------- ENTRY POINT -------- #
if __name__ == "__main__":
    game = Game()
    game.run()