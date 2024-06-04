from __future__ import annotations
from typing import Literal, Type, TYPE_CHECKING
if TYPE_CHECKING:
    from entity import Player

import pygame

from engine import Sprite
from dataclasses import dataclass

import util
from util.constants import *

Direction = Literal["left", "right", "up", "down"]

@dataclass
class Weapon:
    spawn_type: Type[AbstractWeaponInstance]
    animation_key: str = ""
    sound_key: str = ""
    icon_key: str = "error"
    damage: float = 5.0
    cooldown_time: int = 40
    knockback: float = 4.0

class AbstractWeaponInstance(Sprite):
    def __init__(self, parent: Player, stats: Weapon, direction: Direction):
        super().__init__(parent, groups = ["update", "render"])
        self.stats = stats
        self.direction = direction

    def update(self):
        raise NotImplementedError()

class MeleeWeaponAttack(AbstractWeaponInstance):
    def __init__(self, parent: Player, stats: Weapon, direction: Direction) -> None:
        super().__init__(parent, stats, direction)
        self.z_index = 1
        self.remove(self.manager.groups["render"])

        self.life = ANIMATION_FRAME_TIME * 3
        self.stats = stats
        self.rect = pygame.Rect(0, 0, 24 * PIXEL_SCALE, 32 * PIXEL_SCALE)
        self._hit_enemies = [] # keep track of hit enemies

        # flip hitbox if attacking up or down 
        if direction == "up" or direction == "down":
            self.rect.width, self.rect.height = self.rect.height, self.rect.width

        self.direction = direction

        self._stick_to_parent_position()

    def _check_enemy_collisions(self) -> None:
        # check if hitting enemy
        for enemy in self.manager.groups["enemy"].sprites():
            if self.rect.colliderect(enemy.rect) and not enemy in self._hit_enemies:
                enemy.hit(self.manager.get_object("player"), damage = self.stats.damage, kb_magnitude = self.stats.knockback)
                self._hit_enemies.append(enemy)

    def _stick_to_parent_position(self) -> None:
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

    def update(self) -> None:
        self._stick_to_parent_position()
        self._check_enemy_collisions()
        self.life -= self.manager.dt
        if self.life < 0:
            self.kill()

class Fireball(AbstractWeaponInstance):
    def __init__(self, parent: Player, stats: Weapon, direction: Direction):
        super().__init__(parent, stats, direction)

        self.image = pygame.transform.rotate(self.manager.get_image("items/fireball"), util.get_direction_angle(direction) + 90)
        self.rect = self.image.get_rect(center = parent.rect.center)

        self.velocity = pygame.Vector2(util.get_direction_vector(direction)) * 7 + parent.velocity * 0.5
        self.life = 300

        self.room = self.manager.get_object("floor-manager").get_room_at_world_pos(self.rect.center)

    def update(self):
        self.life -= self.manager.dt
        if self.life <= 0:
            # kill with no dying animation
            super().kill()
            return

        self.rect.topleft += self.velocity
        for enemy in self.manager.groups["enemy"]:
            if enemy.rect.colliderect(self):
                enemy.hit(self, damage = self.stats.damage, kb_magnitude = self.stats.knockback)
                self.kill()
                return
            
        for tile in self.room.collide_sprites:
            if self.rect.colliderect(tile.rect):
                self.kill()
                return

class Weapons:
    STARTER_SWORD = Weapon(
        spawn_type = MeleeWeaponAttack,
        animation_key = "sword_attack",
        sound_key = "effect/sword_slash",
        damage = 10.0,
        cooldown_time = ANIMATION_FRAME_TIME * 4,
        knockback = 10.0,
    )

    FIREBALL_SPELL = Weapon(
        spawn_type = Fireball,
        icon_key = "items/fireball",
        damage = 5,
        cooldown_time = 20.0,
        knockback = 3,
    )