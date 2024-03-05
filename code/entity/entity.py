import pygame, random
from engine import Sprite
from .stats import EntityStats
from .bar import HealthBar
from util.constants import *

class Entity(Sprite):
    def __init__(self, parent, stats: EntityStats, hide_health_bar = False):
        super().__init__(parent, groups = ["render", "update"])
        self.velocity = pygame.Vector2()
        self.pos = pygame.Vector2()
        self.stats = stats

        self.health = self.stats.health
        self.iframes = self.stats.iframes

        if not hide_health_bar:
            self.add_child(HealthBar(
                self,
                border_colour = (12, 50, 13),
                border_size = 2,
                health_colour = (255, 10, 10),
                health_height = 4,
            ))

    # both collision functions take the future position of the hitbox
    # and check if it intersects with an obstical
    # if this is true, then move the player hitbox so that it is touching the 
    # edge of the obstical
    def check_collision_vertical(self):
        future_player_rect = pygame.Rect(self.pos.x, self.pos.y, self.rect.width, self.rect.height)
        for sprite in self.manager.groups["collide"].sprites():
            if sprite == self: continue
            if sprite.rect.colliderect(future_player_rect):
                if self.velocity.y > 0:
                    future_player_rect.bottom = sprite.rect.top
                    self.pos = pygame.Vector2(future_player_rect.topleft)
                    return
                elif self.velocity.y < 0:
                    future_player_rect.top = sprite.rect.bottom
                    self.pos = pygame.Vector2(future_player_rect.topleft)
                    return

    def check_collision_horizontal(self):
        future_player_rect = pygame.Rect(self.pos.x, self.pos.y, self.rect.width, self.rect.height)
        for sprite in self.manager.groups["collide"].sprites():
            if sprite == self: continue
            if sprite.rect.colliderect(future_player_rect):
                if self.velocity.x > 0:
                    future_player_rect.right = sprite.rect.left
                    self.pos = pygame.Vector2(future_player_rect.topleft)
                    return
                elif self.velocity.x < 0:
                    future_player_rect.left = sprite.rect.right
                    self.pos = pygame.Vector2(future_player_rect.topleft)
                    return

    def add_velocity(self, velocity: pygame.Vector2):
        "Adds velocity to entity, i.e a force in an instant."
        self.velocity += velocity

    def hit(self, other, damage = 0, kb_magnitude = 0):
        if self.iframes == 0:
            kbv = self.pos - other.pos
            kbv.scale_to_length(kb_magnitude)
            self.add_velocity(kbv)

            self.iframes = self.stats.iframes

            self.health -= damage

            if self.health <= 0:
                self.kill()

    def move(self):
        # checking collisions of one direction at a time
        # ensures that an overlap of bounds is due to the
        # movement of one direction
        self.pos.x += self.velocity.x * self.manager.dt
        self.check_collision_horizontal()
        self.pos.y += self.velocity.y * self.manager.dt
        self.check_collision_vertical()

        # exponentially reduce entity speed
        self.velocity.x /= SURFACE_FRICTION_COEFFICIENT
        self.velocity.y /= SURFACE_FRICTION_COEFFICIENT
        # prevent really small numbers
        if -0.01 < self.velocity.x < 0.01: self.velocity.x = 0
        if -0.01 < self.velocity.y < 0.01: self.velocity.y = 0

        # readjust hitbox to precise position
        self.rect.topleft = self.pos

    def update(self):
        super().update()
        self.move()
        self.iframes -= self.manager.dt
        if self.iframes < 0:
            self.iframes = 0
