from pathlib import Path

import pygame


class BackgroundRenderer:
    def __init__(self):
        self.original = None
        self.cached = None
        self.cached_size = None

        asset_dir = Path(__file__).resolve().parents[2] / "assets" / "backgrounds"
        candidates = [
            asset_dir / "bg-img.png",
            asset_dir / "bg-img.jpg",
            asset_dir / "bg-img.jpeg",
            asset_dir / "bg-image.jpg",
            asset_dir / "bg-image.png",
            asset_dir / "bg-image.jpeg",
            asset_dir / "background.jpg",
            asset_dir / "background.png",
            asset_dir / "background.jpeg",
        ]

        for image_path in candidates:
            if not image_path.exists():
                continue
            try:
                self.original = pygame.image.load(image_path.as_posix()).convert()
                break
            except pygame.error:
                self.original = None

    def draw(self, screen):
        if self.original is None:
            screen.fill((10, 8, 8))
            return

        size = screen.get_size()
        if self.cached is None or self.cached_size != size:
            self.cached = pygame.transform.smoothscale(self.original, size)
            self.cached_size = size

        screen.blit(self.cached, (0, 0))
