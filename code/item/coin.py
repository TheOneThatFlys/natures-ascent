import pygame, random

from engine import Sprite, AnimationManager, Node
from engine.types import *
from util import parse_spritesheet

class Coin(Sprite):
    def __init__(self, parent: Node, position: Vec2, randomness: int = 16) -> None:
        super().__init__(parent, ["render", "update"])

        self.am = AnimationManager(self)
        self.am.add_animation("spin", parse_spritesheet(self.manager.get_image("items/coin"), frame_count = 4))
        self.image = self.am.set_animation("spin")
        self.rect = self.image.get_rect(center = (position[0] + random.randint(-randomness, randomness), position[1] + random.randint(-randomness, randomness)))
        self.pos = pygame.Vector2(self.rect.center)

        self.player = self.manager.get_object("player")

    def kill(self) -> None:
        self.manager.play_sound("effect/coin", 0.05)
        self.player.add_money(value = 1)
        super().kill()

    def update(self) -> None:
        self.am.update()

        # vector from player to coin
        delta_v = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)

        if delta_v.magnitude() < self.player.stats.pickup_range:
            self.pos += delta_v.normalize() * self.manager.dt

        self.rect.center = self.pos

        if self.rect.colliderect(self.player.rect):
            self.kill()