from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from entity import Player

import pygame, random

from engine import Sprite, AnimationManager, Node
from engine.types import *
from util import parse_spritesheet

class Pickup(Sprite):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, ["render", "update"])

        self.animation_manager = self.add_child(AnimationManager(self))
        self.pos = pygame.Vector2(position)

        self.player: Player = self.manager.get_object("player")

    def update(self) -> None:
        self.animation_manager.update()

        # vector from player to pickup
        delta_v = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
        if delta_v.magnitude() < self.player.stats.pickup_range:
            self.pos += delta_v.normalize() * self.manager.dt

        self.rect.center = self.pos

        if self.rect.colliderect(self.player.hitbox):
            self.on_pickup()
            self.kill()

    def on_pickup(self) -> None:
        raise NotImplementedError()

class Coin(Pickup):
    def __init__(self, parent: Node, position: Vec2, randomness: int = 16) -> None:
        super().__init__(parent, (position[0] + random.randint(-randomness, randomness), position[1] + random.randint(-randomness, randomness)))

        self.animation_manager.add_animation("spin", parse_spritesheet(self.manager.get_image("items/coin", 0.5), frame_count = 4))
        self.image = self.animation_manager.set_animation("spin")
        self.rect = self.image.get_rect(center = self.pos)

    def on_pickup(self) -> None:
        self.manager.play_sound("effect/coin", 0.05)
        self.player.inventory.add_coin(value = 1)
 
class Health(Pickup):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, position)

        self.animation_manager.add_animation("beat", parse_spritesheet(self.manager.get_image("items/heart"), frame_count = 4))
        self.image = self.animation_manager.set_animation("beat")
        self.rect = self.image.get_rect(center = self.pos)

    def on_pickup(self) -> None:
        self.manager.play_sound("effect/health_pickup", 0.2)
        self.player.add_health(20)