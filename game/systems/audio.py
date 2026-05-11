from pathlib import Path

import pygame


class SilentSound:
    def play(self):
        return None


class Audio:
    def __init__(self):
        self.coin = SilentSound()
        self.gameover = SilentSound()
        self.music_on = False
        self.sound_on = True

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            return

        base_dir = Path(__file__).resolve().parents[2]
        coin_path = base_dir / "assets" / "sounds" / "coin.mp3"
        gameover_path = base_dir / "assets" / "sounds" / "gameover.mp3"
        music_path = base_dir / "assets" / "music" / "music.wav"

        try:
            self.coin = pygame.mixer.Sound(coin_path)
        except pygame.error:
            self.coin = SilentSound()

        try:
            self.gameover = pygame.mixer.Sound(gameover_path)
        except pygame.error:
            self.gameover = SilentSound()

        self.music_volume = 0.5
        self.sound_volume = 0.8

        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
            self.music_on = True
        except pygame.error:
            self.music_on = False

        # apply to sound effects if loaded
        try:
            self.coin.set_volume(self.sound_volume)
            self.gameover.set_volume(self.sound_volume)
        except Exception:
            pass

    def play_coin(self):
        if self.sound_on:
            self.coin.play()

    def play_gameover(self):
        if self.sound_on:
            self.gameover.play()

    def stop_music(self):
        if self.music_on:
            pygame.mixer.music.stop()
            self.music_on = False

    def pause_music(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()

    def unpause_music(self):
        try:
            if not pygame.mixer.music.get_busy() and self.music_on:
                pygame.mixer.music.unpause()
        except pygame.error:
            pass

    def set_music_volume(self, value):
        self.music_volume = max(0.0, min(1.0, value))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except pygame.error:
            pass
        if self.music_volume <= 0:
            self.music_on = False
        else:
            self.music_on = True

    def set_sound_volume(self, value):
        self.sound_volume = max(0.0, min(1.0, value))
        try:
            self.coin.set_volume(self.sound_volume)
            self.gameover.set_volume(self.sound_volume)
        except Exception:
            pass
        self.sound_on = self.sound_volume > 0

    def change_music_volume(self, delta):
        self.set_music_volume(self.music_volume + delta)

    def change_sound_volume(self, delta):
        self.set_sound_volume(self.sound_volume + delta)

    def toggle_music(self):
        if self.music_on:
            self.pause_music()
            self.music_on = False
        else:
            self.music_on = True
            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass

    def toggle_sound(self):
        self.sound_on = not self.sound_on
        if self.sound_on:
            self.set_sound_volume(self.sound_volume if self.sound_volume > 0 else 0.5)
        else:
            self.set_sound_volume(0)


