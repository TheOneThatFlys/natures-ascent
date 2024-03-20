import pygame
from typing import Literal

from engine import Node, Sprite

from dataclasses import dataclass

Direction = Literal["left", "right", "up", "down"]

@dataclass
class WeaponStats:
    size: tuple[int, int] = (100, 50)
    damage: float = 5.0
    attack_time: int = 40
    knockback: float = 4.0

class MeleeWeaponAttack(Sprite):
    def __init__(self, parent: Node, stats: WeaponStats, direction: Direction):
        super().__init__(parent, groups = ["update"])
        self.id = "player_attack"

        self.rect = pygame.Rect(0, 0, *stats.size)
        self._hit_enemies = [] # keep track of hit enemies

        # flip hitbox if attacking up or down 
        if direction == "up" or direction == "down":
            self.rect.width, self.rect.height = self.rect.height, self.rect.width

        self.direction = direction

        self._stick_to_parent_position()

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