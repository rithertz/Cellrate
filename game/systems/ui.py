import pygame

from game.config import ACCENT, GRAY, LIGHT_GRAY, WHITE

pygame.font.init()


def get_font(size, bold=False):
    try:
        return pygame.font.SysFont("SF Pro Display", size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size, bold=bold)


def draw_text(screen, text, size, color, x, y, center=True, bold=False, shadow=True):
    font = get_font(size, bold)
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    if shadow:
        shadow_surface = font.render(text, True, GRAY)
        shadow_rect = rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        screen.blit(shadow_surface, shadow_rect)
    screen.blit(surface, rect)


def draw_button(screen, text, x, y, w, h, active=False, font_size=28, muted=False):
    if muted and not active:
        color = (102, 102, 102)
        border_color = (78, 78, 78)
        text_color = (228, 228, 228)
    else:
        color = LIGHT_GRAY if not active else ACCENT
        border_color = ACCENT if active else GRAY
        text_color = WHITE
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, color, rect, border_radius=16)
    pygame.draw.rect(screen, border_color, rect, width=2, border_radius=16)
    draw_text(screen, text, font_size, text_color, x + w // 2, y + h // 2, center=True, bold=True, shadow=False)


def draw_pause_button(screen, rect, active=False):
    fill = ACCENT if active else (34, 34, 34)
    border = WHITE if active else GRAY
    pygame.draw.ellipse(screen, fill, rect)
    pygame.draw.ellipse(screen, border, rect, width=2)

    bar_width = max(4, rect.width // 8)
    gap = bar_width + 2
    bar_height = rect.height // 2
    left_bar = pygame.Rect(0, 0, bar_width, bar_height)
    right_bar = pygame.Rect(0, 0, bar_width, bar_height)
    left_bar.center = (rect.centerx - gap // 2, rect.centery)
    right_bar.center = (rect.centerx + gap // 2, rect.centery)
    pygame.draw.rect(screen, WHITE, left_bar, border_radius=3)
    pygame.draw.rect(screen, WHITE, right_bar, border_radius=3)


def draw_stat_card(screen, rect, title, value, accent=ACCENT, alpha=150, title_size=18, value_size=34, align_left=False):
    surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surface, (26, 26, 26, alpha), surface.get_rect(), border_radius=20)
    pygame.draw.rect(surface, (*accent, min(255, alpha + 45)), surface.get_rect(), width=2, border_radius=20)
    screen.blit(surface, rect.topleft)
    title_y = rect.y + rect.height * 0.28
    value_y = rect.y + rect.height * 0.66
    if align_left:
        draw_text(screen, title, title_size, GRAY, rect.x + 16, int(title_y) - 6, center=False, bold=True, shadow=False)
        draw_text(screen, str(value), value_size, WHITE, rect.x + 16, int(value_y) - 10, center=False, bold=True, shadow=False)
    else:
        draw_text(screen, title, title_size, GRAY, rect.centerx, int(title_y), center=True, bold=True, shadow=False)
        draw_text(screen, str(value), value_size, WHITE, rect.centerx, int(value_y), center=True, bold=True, shadow=False)


def draw_panel(screen, rect):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (12, 12, 12, 210), panel.get_rect(), border_radius=28)
    pygame.draw.rect(panel, (255, 255, 255, 45), panel.get_rect(), width=2, border_radius=28)
    screen.blit(panel, rect.topleft)
