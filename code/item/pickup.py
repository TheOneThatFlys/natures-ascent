from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entity import Player

import pygame, random

from engine import Sprite, AnimationManager, Node
from engine.types import *
from util import parse_spritesheet
from util.constants import *

class Pickup(Sprite):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent, ["render", "update"])
        self.animation_manager = self.add_child(AnimationManager(self))
        self.player: Player = self.manager.get_object("player")

    def update(self) -> None:
        self.animation_manager.update()

        # vector from player to pickup
        delta_v = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
        if delta_v.magnitude() < self.player.stats.pickup_range:
            self.rect.center += delta_v.normalize() * self.manager.dt

        if self.rect.colliderect(self.player.hitbox):
            self.on_pickup()
            self.kill()

    def on_pickup(self) -> None:
        raise NotImplementedError()

class Coin(Pickup):
    def __init__(self, parent: Node, position: Vec2, randomness: int = 16) -> None:
        super().__init__(parent)

        self.animation_manager.add_animation("spin", parse_spritesheet(self.manager.get_image("items/coin", 0.5), frame_count = 4))
        self.image = self.animation_manager.set_animation("spin")
        self.rect = self.image.get_rect(center = (position[0] + random.randint(-randomness, randomness), position[1] + random.randint(-randomness, randomness)))

    def on_pickup(self) -> None:
        self.manager.play_sound("effect/coin", 0.05)
        self.player.inventory.add_coin(value = 1)
 
class Health(Pickup):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent)

        self.animation_manager.add_animation("beat", parse_spritesheet(self.manager.get_image("items/heart"), frame_count = 4))
        self.image = self.animation_manager.set_animation("beat")
        self.rect = self.image.get_frect(center = position)
        self.velocity = pygame.Vector2()

        # max distance (ish) from the player while touching it (corner to corner distance)
        self.max_distance = (pygame.Vector2(self.rect.size) / 2).magnitude() + (pygame.Vector2(self.player.hitbox.size) / 2).magnitude()

    def update(self) -> None:
        # override follow logic - run away from player when on full health
        self.animation_manager.update()
        if self.rect.colliderect(self.player.hitbox):
            if self.player.health == self.player.stats.health:
                # avoid player
                delta_v = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
                multiplier = (self.max_distance - delta_v.magnitude()) / self.max_distance
                self.velocity += -delta_v.normalize() * multiplier
            else:
                self.on_pickup()
                self.kill()

        self.velocity -= self.velocity * SURFACE_FRICTION_COEFFICIENT * self.manager.dt

        self.rect.x += self.velocity.x * self.manager.dt
        for s in self.manager.groups["collide"]:
            if not s.rect.colliderect(self.rect): continue
            if self.velocity.x < 0: self.rect.x = s.rect.right
            elif self.velocity.x > 0: self.rect.right = s.rect.x

        self.rect.y += self.velocity.y * self.manager.dt
        for s in self.manager.groups["collide"]:
            if not s.rect.colliderect(self.rect): continue
            if self.velocity.y < 0: self.rect.y = s.rect.bottom
            elif self.velocity.y > 0: self.rect.bottom = s.rect.y

    def on_pickup(self) -> None:
        self.manager.play_sound("effect/health_pickup", 0.2)
        self.player.add_health(20)