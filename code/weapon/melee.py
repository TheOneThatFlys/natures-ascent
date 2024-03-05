import pygame
from typing import Literal

from engine import Node, Sprite
from .stats import WeaponStats

Direction = Literal["left", "right", "up", "down"]

class MeleeWeaponAttack(Sprite):
    def __init__(self, parent: Node, image: pygame.Surface, stats: WeaponStats, direction: Direction):
        super().__init__(parent, groups = ["update", "render"])

        self.rect = pygame.Rect(0, 0, *stats.size)
        self._hit_enemies = [] # keep track of hit enemies

        # flip hitbox if attacking up or down 
        if direction == "up" or direction == "down":
            self.rect.width, self.rect.height = self.rect.height, self.rect.width

        self.direction = direction

        rotation_factor = 0
        self._stick_to_parent_position()
        if direction == "right":
            rotation_factor = 180
        elif direction == "down":
            rotation_factor = 270
        elif direction == "up":
            rotation_factor = 90

        self.image = pygame.transform.rotate(image, rotation_factor)
        self.life = stats.attack_time
        self.stats = stats

    def _check_enemy_collisions(self):
        # check if hitting enemy
        for enemy in self.manager.groups["enemy"].sprites():
            if self.rect.colliderect(enemy.rect) and not enemy in self._hit_enemies:
                enemy.hit(self.manager.get_object_from_id("player"), damage = self.stats.damage, kb_magnitude = self.stats.knockback)
                self._hit_enemies.append(enemy)

    def _stick_to_parent_position(self):
        # stick hitbox to a side based on direction of attack
        if self.direction == "left":
            self.rect.right = self.parent.rect.left
            self.rect.centery = self.parent.rect.centery 
        elif self.direction == "right":
            self.rect.left = self.parent.rect.right
            self.rect.centery = self.parent.rect.centery 
        elif self.direction == "down":
            self.rect.top = self.parent.rect.bottom
            self.rect.centerx = self.parent.rect.centerx
        elif self.direction == "up":
            self.rect.bottom = self.parent.rect.top
            self.rect.centerx = self.parent.rect.centerx

    def update(self):
        self._stick_to_parent_position()
        self._check_enemy_collisions()
        self.life -= self.manager.dt
        if self.life < 0:
            self.kill()