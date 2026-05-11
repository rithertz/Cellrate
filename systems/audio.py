import pygame
import os


class Audio:
    def __init__(self):
        pygame.mixer.init()

        # ---------------- BASE PATH ---------------- #
        # Gets project root directory
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # ---------------- FILE PATHS ---------------- #
        self.coin_path = os.path.join(BASE_DIR, "assets", "sounds", "coin.mp3")
        self.gameover_path = os.path.join(BASE_DIR, "assets", "sounds", "gameover.mp3")
        self.music_path = os.path.join(BASE_DIR, "assets", "music", "music.wav")

        # ---------------- LOAD SOUNDS ---------------- #
        self.coin = pygame.mixer.Sound(self.coin_path)
        self.gameover = pygame.mixer.Sound(self.gameover_path)

        # ---------------- LOAD MUSIC ---------------- #
        pygame.mixer.music.load(self.music_path)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)  # loop forever

    # ---------------- PLAY METHODS ---------------- #
    def play_coin(self):
        self.coin.play()

    def play_gameover(self):
        self.gameover.play()