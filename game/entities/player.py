import pygame

from game.config import ACCENT, RED


class Player:
    def __init__(self, x, y, size, speed):
        self.rect = pygame.Rect(x, y, size, size)
        self.position = pygame.Vector2(float(x), float(y))
        self.velocity = pygame.Vector2(0, 0)

        self.base_speed = float(speed)
        self.speed = float(speed)
        self.acceleration = 0.26
        self.coast_drag = 0.055
        self.counter_brake = 0.34
        self.color = RED

        self.trails = []
        self.trail_tick = 0
        self.input_hold_frames = 0

        self.invulnerable_frames = 0
        self.slow_frames = 0
        self.slow_factor = 1.0

    @property
    def is_invulnerable(self):
        return self.invulnerable_frames > 0

    def handle_input(self, speed_scale=1.0):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y += 1

        if direction.length_squared() > 0:
            self.input_hold_frames += 1
            self.apply_direction(direction, self.input_hold_frames, speed_scale=speed_scale)
        else:
            self.input_hold_frames = 0

    def apply_direction(self, direction, hold_frames=0, speed_scale=1.0):
        self.velocity = self.advance_velocity(
            self.velocity,
            direction,
            hold_frames,
            self.get_speed_cap(hold_frames, speed_scale=speed_scale),
            self.acceleration,
            self.coast_drag,
            self.counter_brake,
        )

    def update(self, width, height, handle_input=True, wraparound=False, speed_scale=1.0, external_force=None):
        if handle_input:
            self.handle_input(speed_scale=speed_scale)
        elif self.input_hold_frames == 0:
            self.velocity = self.advance_velocity(
                self.velocity,
                (0, 0),
                0,
                self.get_speed_cap(0, speed_scale=speed_scale),
                self.acceleration,
                self.coast_drag,
                self.counter_brake,
            )

        if handle_input and self.input_hold_frames == 0:
            self.velocity = self.advance_velocity(
                self.velocity,
                (0, 0),
                0,
                self.get_speed_cap(0, speed_scale=speed_scale),
                self.acceleration,
                self.coast_drag,
                self.counter_brake,
            )

        if external_force is not None:
            self.velocity += pygame.Vector2(external_force)

        self.position += self.velocity
        self._sync_rect()
        self._constrain(width, height, wraparound)
        self._update_status_effects()
        self._update_trails()

    def apply_bot_control(self, dx, dy, width, height, wraparound=False, speed_scale=1.0, external_force=None):
        if dx or dy:
            self.input_hold_frames += 1
            self.apply_direction((dx, dy), self.input_hold_frames, speed_scale=speed_scale)
        else:
            self.input_hold_frames = 0
        self.update(
            width,
            height,
            handle_input=False,
            wraparound=wraparound,
            speed_scale=speed_scale,
            external_force=external_force,
        )

    def grant_invulnerability(self, duration_frames):
        self.invulnerable_frames = max(self.invulnerable_frames, int(duration_frames))

    def apply_slow(self, duration_frames, factor):
        self.slow_frames = max(self.slow_frames, int(duration_frames))
        self.slow_factor = min(self.slow_factor, float(factor))

    def clear_status_effects(self):
        self.invulnerable_frames = 0
        self.slow_frames = 0
        self.slow_factor = 1.0

    def increase_speed(self, amount):
        self.speed += amount

    def get_speed_cap(self, hold_frames, speed_scale=1.0):
        return (self.speed + min(4.3, hold_frames * 0.07)) * speed_scale * self._status_speed_scale()

    def set_position(self, x, y):
        self.position.update(float(x), float(y))
        self._sync_rect()

    def reset(self, position=None):
        if position is None:
            position = (100.0, 100.0)
        self.position.update(float(position[0]), float(position[1]))
        self.velocity.update(0, 0)
        self.speed = self.base_speed
        self.trails.clear()
        self.trail_tick = 0
        self.input_hold_frames = 0
        self.clear_status_effects()
        self._sync_rect()

    def draw(self, screen):
        if self.trails:
            trail_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            for trail in self.trails:
                alpha = max(0, min(255, int(trail["life"] * 255)))
                radius = max(4, int(trail["size"]))
                color = (*trail["color"], alpha)
                pygame.draw.circle(trail_surface, color, trail["pos"], radius)
            screen.blit(trail_surface, (0, 0))

        fill = ACCENT if self.is_invulnerable and (self.invulnerable_frames // 8) % 2 == 0 else self.color
        pygame.draw.rect(screen, fill, self.rect, border_radius=10)
        if self.slow_frames > 0:
            pygame.draw.rect(screen, (180, 220, 255), self.rect, width=2, border_radius=10)

    def _constrain(self, width, height, wraparound):
        if wraparound:
            if self.rect.right < 0:
                self.position.x = width - 1
            elif self.rect.left > width:
                self.position.x = -self.rect.width + 1

            if self.rect.bottom < 0:
                self.position.y = height - 1
            elif self.rect.top > height:
                self.position.y = -self.rect.height + 1

            self._sync_rect()
            return

        hit_wall = False

        if self.position.x < 0:
            self.position.x = 0
            self.velocity.x = 0
            hit_wall = True
        elif self.position.x > width - self.rect.width:
            self.position.x = width - self.rect.width
            self.velocity.x = 0
            hit_wall = True

        if self.position.y < 0:
            self.position.y = 0
            self.velocity.y = 0
            hit_wall = True
        elif self.position.y > height - self.rect.height:
            self.position.y = height - self.rect.height
            self.velocity.y = 0
            hit_wall = True

        self._sync_rect()

        if hit_wall and self.velocity.length_squared() < 0.01:
            self.velocity.update(0, 0)

    def _status_speed_scale(self):
        return self.slow_factor if self.slow_frames > 0 else 1.0

    def _update_status_effects(self):
        if self.invulnerable_frames > 0:
            self.invulnerable_frames -= 1
        if self.slow_frames > 0:
            self.slow_frames -= 1
            if self.slow_frames == 0:
                self.slow_factor = 1.0

    def _sync_rect(self):
        self.rect.x = int(round(self.position.x))
        self.rect.y = int(round(self.position.y))

    def _update_trails(self):
        self.trail_tick += 1
        speed_ratio = 0.0
        if self.speed > 0:
            speed_ratio = min(1.0, self.velocity.length() / max(0.01, self.speed))

        if speed_ratio > 0.08 and self.trail_tick % 2 == 0:
            trail_color = ACCENT if self.is_invulnerable else self.color
            self.trails.append(
                {
                    "pos": (self.rect.centerx, self.rect.centery),
                    "life": 0.55 + speed_ratio * 0.25,
                    "size": self.rect.width * (0.18 + speed_ratio * 0.14),
                    "color": trail_color,
                }
            )

        next_trails = []
        for trail in self.trails:
            trail["life"] -= 0.045
            trail["size"] *= 0.985
            if trail["life"] > 0:
                next_trails.append(trail)
        self.trails = next_trails

    @staticmethod
    def advance_velocity(velocity, direction, hold_frames, speed_cap, acceleration, coast_drag, counter_brake):
        next_velocity = pygame.Vector2(velocity)
        direction_vector = pygame.Vector2(direction)

        if direction_vector.length_squared() > 0:
            if direction_vector.length_squared() > 1:
                direction_vector = direction_vector.normalize()
            startup_boost = max(0.0, 0.2 - max(0, hold_frames - 1) * 0.045)
            axis_acceleration = acceleration + startup_boost + min(0.62, hold_frames * 0.018)
            next_velocity.x = Player._advance_axis(next_velocity.x, direction_vector.x, axis_acceleration, coast_drag, counter_brake)
            next_velocity.y = Player._advance_axis(next_velocity.y, direction_vector.y, axis_acceleration, coast_drag, counter_brake)
        else:
            next_velocity *= max(0.0, 1.0 - coast_drag)

        if next_velocity.length() > speed_cap:
            next_velocity.scale_to_length(speed_cap)
        if next_velocity.length_squared() < 0.0025:
            next_velocity.update(0, 0)
        return next_velocity

    @staticmethod
    def _advance_axis(current_velocity, direction_input, axis_acceleration, coast_drag, counter_brake):
        if abs(direction_input) < 0.01:
            return current_velocity * max(0.0, 1.0 - coast_drag * 0.7)

        if current_velocity * direction_input < -0.05:
            current_velocity += direction_input * (counter_brake + axis_acceleration * 0.55)
            if current_velocity * direction_input > 0:
                current_velocity *= 0.32
            return current_velocity

        return current_velocity + direction_input * axis_acceleration
