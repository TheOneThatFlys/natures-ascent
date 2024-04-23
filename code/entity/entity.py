import pygame
from typing import Literal
from engine import Sprite, AnimationManager, Node
from util.constants import *

from .stats import EntityStats
from .bar import HealthBar

HealthBarMode = Literal["normal", "always-show", "always-hide"]

class Entity(Sprite):
    def __init__(self, parent: Node, stats: EntityStats, health_bar_mode: HealthBarMode = "normal") -> None:
        super().__init__(parent, groups = ["render", "update"])
        self.velocity = pygame.Vector2()
        self.stats = stats

        self.animation_manager: AnimationManager = self.add_child(AnimationManager(self))

        self.health = self.stats.health
        self.iframes = 0

        self.health_bar_mode = health_bar_mode
        self.time_since_hit = HEALTH_VISIBILITY_TIME + 1
        self.health_bar = self.add_child(
            HealthBar(
                self,
                border_colour = (0, 0, 0),
                border_size = 2,
                health_colour = (255, 10, 10),
            )
        )

        self.hitbox_squish = 2

        if health_bar_mode == "always-hide" or health_bar_mode == "normal":
            self.health_bar.hide()
        else:
            self.health_bar.show()

    def check_collision_vertical(self, collide_group: list[Sprite]) -> None:
        if self.velocity.y == 0: return
        # get future position of hitbox
        future_collision_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height / self.hitbox_squish, self.rect.width, self.rect.height / self.hitbox_squish)
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
        future_collision_rect = pygame.Rect(self.rect.x, self.rect.y + self.rect.height / self.hitbox_squish, self.rect.width, self.rect.height / self.hitbox_squish)
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

    def hit(self, other: Sprite, damage: float = 0, kb_magnitude: float = 0) -> None:
        if self.iframes == 0:
            kbv = pygame.Vector2(self.rect.center) - other.rect.center
            kbv.scale_to_length(kb_magnitude)
            self.add_velocity(kbv)

            self.iframes = self.stats.iframes

            self.health -= damage

            if self.health <= 0:
                self.kill()

            self.time_since_hit = 0

            self.on_hit(other)

    def on_hit(self, other: Sprite) -> None:
        pass

    def apply_friction(self):
        self.velocity -= self.velocity * SURFACE_FRICTION_COEFFICIENT * self.manager.dt
        # prevent small values of velocity
        if -0.01 < self.velocity.x < 0.01: self.velocity.x = 0
        if -0.01 < self.velocity.y < 0.01: self.velocity.y = 0

    def move(self) -> None:
        # checking collisions of one direction at a time
        # ensures that an overlap of bounds is due to the
        # movement of one direction
        self.rect.x += self.velocity.x * self.manager.dt
        self.check_collision_horizontal(self.manager.groups["collide"])
        self.rect.y += self.velocity.y * self.manager.dt
        self.check_collision_vertical(self.manager.groups["collide"])

        self.apply_friction()

    def update(self) -> None:
        super().update()
        self.move()
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