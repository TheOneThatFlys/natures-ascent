from __future__ import annotations

import pygame, random
from typing import Literal
from engine import Sprite, AnimationManager, Node
from util.constants import *
from util import polar_to_cart

from .stats import EntityStats
from .bar import HealthBar

HealthBarMode = Literal["normal", "always-show", "always-hide"]

class Entity(Sprite):
    """
    Class representing a sprite that has health with colliders, i.e player and enemies.
    
    ``self.image``, ``self.rect`` and optionally ``self._hitbox`` need to be defined in subclasses.
    """
    def __init__(self, parent: Node, stats: EntityStats, health_bar_mode: HealthBarMode = "normal") -> None:
        super().__init__(parent, groups = ["render", "update"])
        self.velocity = pygame.Vector2()
        self.stats = stats

        self.animation_manager: AnimationManager = self.add_child(AnimationManager(self))

        self.health = self.stats.health
        self.iframes = 0

        self.health_bar_mode = health_bar_mode
        self.time_since_hit = HEALTH_VISIBILITY_TIME + 1
        self.local_friction_coef = SURFACE_FRICTION_COEFFICIENT
        self.health_bar = self.add_child(
            HealthBar(
                self,
                border_colour = UI_DARKBROWN,
                border_size = 2,
                health_colour = ENEMY_RED,
            )
        )

        self.collision_box_squish = 2
        self.collision_active = True

        if health_bar_mode == "always-hide" or health_bar_mode == "normal":
            self.health_bar.hide()
        else:
            self.health_bar.show()

        self.hitbox_offset = pygame.Vector2()

    @property
    def hitbox(self) -> pygame.Rect:
        return getattr(self, "_hitbox", self.rect)
        
    @hitbox.setter
    def hitbox(self, value: pygame.Rect) -> None:
        self._hitbox = value

    def collides(self, other: Entity) -> bool:
        return self.hitbox.colliderect(other.hitbox)

    def check_collision_vertical(self, collide_group: list[Sprite]) -> None:
        if self.velocity.y == 0: return
        # get future position of hitbox
        future_collision_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height / self.collision_box_squish, self.rect.width, self.rect.height / self.collision_box_squish)
        for sprite in collide_group:
            if sprite == self: continue
            if sprite.rect.colliderect(future_collision_rect):
                # move self so that it no longer colliding
                if self.velocity.y > 0:
                    self.rect.bottom = sprite.rect.top
                    return
                elif self.velocity.y < 0:
                    future_collision_rect.top = sprite.rect.bottom
                    self.rect.bottom = future_collision_rect.bottom
                    return

    def check_collision_horizontal(self, collide_group: list[Sprite]) -> None:
        if self.velocity.x == 0: return
        # see Entity.check_collision_vertical()
        future_collision_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height / self.collision_box_squish, self.rect.width, self.rect.height / self.collision_box_squish)
        for sprite in collide_group:
            if sprite == self: continue
            if sprite.rect.colliderect(future_collision_rect):
                if self.velocity.x > 0:
                    self.rect.right = sprite.rect.left
                    return
                elif self.velocity.x < 0:
                    self.rect.left = sprite.rect.right
                    return

    def add_velocity(self, velocity: pygame.Vector2) -> None:
        "Adds velocity to entity, i.e a force in an instant."
        self.velocity += velocity

    def hit(self, other: Sprite, damage: float = 0, kb_magnitude: float = 0) -> bool:
        """Attempt to hit this entity. Returns True if hit was successful."""
        if self.iframes == 0:
            kbv = pygame.Vector2(self.rect.center) - other.rect.center
            if kb_magnitude == 0:
                kbv = pygame.Vector2(0, 0)
            elif kbv.magnitude() == 0:
                kbv = polar_to_cart(random.randint(0, 360), kb_magnitude)
            else:
                kbv.scale_to_length(kb_magnitude)
            self.add_velocity(kbv)

            self.iframes = self.stats.iframes

            self.health -= damage
            self.on_hit(other)
            self.time_since_hit = 0

            if self.health <= 0:
                self.kill()
            return True
        return False

    def on_hit(self, other: Sprite) -> None:
        pass

    def apply_friction(self):
        self.velocity -= self.velocity * self.local_friction_coef * self.manager.dt
        # prevent small values of velocity
        if -0.01 < self.velocity.x < 0.01: self.velocity.x = 0
        if -0.01 < self.velocity.y < 0.01: self.velocity.y = 0

    def move(self) -> None:
        # checking collisions of one direction at a time
        # ensures that an overlap of bounds is due to the
        # movement of one direction
        self.rect.x += self.velocity.x * self.manager.dt
        if self.collision_active: self.check_collision_horizontal(self.manager.groups["collide"])
        self.rect.y += self.velocity.y * self.manager.dt
        if self.collision_active: self.check_collision_vertical(self.manager.groups["collide"])

        self.apply_friction()

    def update(self) -> None:
        super().update()
        self.move()
        self.hitbox.center = self.rect.center + self.hitbox_offset
        self.animation_manager.update()
        self.iframes -= self.manager.dt
        if self.iframes < 0:
            self.iframes = 0

        if self.health_bar_mode == "normal":
            if self.time_since_hit < HEALTH_VISIBILITY_TIME:
                self.time_since_hit += self.manager.dt
                self.health_bar.show()
            else:
                self.health_bar.hide()