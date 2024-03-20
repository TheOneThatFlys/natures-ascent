import pygame

from engine import Sprite, AnimationManager
from util import parse_spritesheet

class Coin(Sprite):
    def __init__(self, parent, position):
        super().__init__(parent, ["render", "update"])

        self.am = AnimationManager(self)
        self.am.add_animation("spin", parse_spritesheet(self.manager.get_image("items/coin"), frame_count = 4))
        self.image = self.am.set_animation("spin")
        self.rect = self.image.get_rect(center = position)

        self.player = self.manager.get_object_from_id("player")

    def kill(self):
        self.manager.play_sound("effect/coin", 0.5)
        super().kill()

    def update(self):
        self.am.update()
        if self.rect.colliderect(self.player.rect):
            self.kill()