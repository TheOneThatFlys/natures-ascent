from __future__ import annotations
from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from entity import Player, Entity
    from world import FloorManager

import pygame, math

from engine import Sprite, Node
from engine.types import *

import util
from util.constants import *

class Weapon(Node):
    """
    Stores weapon information such as sound effects and icon keys.
    Actual implementation for attacks should be in derived classes.
    """
    def __init__(self, parent: Player, animation_key: str = "", sound_key: str = "", icon_key: str = "error", cooldown_time: int = 40) -> None:
        super().__init__(parent)
        self.player = parent

        self.animation_key = animation_key
        self.sound_key = sound_key
        self.icon_key = icon_key
        self.cooldown_time = cooldown_time

    def attack(self, direction: Direction) -> None:
        if self.sound_key:
            self.manager.play_sound(self.sound_key, volume=0.2)

class Spell(Weapon):
    """
    Same as a weapon, but attack direction does not matter (as it is binded to a single key)
    """
    def attack(self) -> None:
        super().attack(None)

class Sword(Weapon):
    def __init__(self, parent: Player):
        super().__init__(
            parent,
            animation_key = "sword_attack",
            sound_key = "effect/sword_slash",
            icon_key = "items/sword",
            cooldown_time = ANIMATION_FRAME_TIME * 4,
        )

        self.damage = 10.0
        self.knockback = 10.0

    def attack(self, direction: Direction) -> None:
        super().attack(direction)
        self.player.add_child(MeleeWeaponAttack(self.player, direction, self.damage, self.knockback))

class MeleeWeaponAttack(Sprite):
    def __init__(self, parent: Player, direction: Direction, damage: float, knockback: float) -> None:
        super().__init__(parent, groups = ["update"])
        self.z_index = 1
        self.direction = direction
        self.damage = damage
        self.knockback = knockback

        self.life = ANIMATION_FRAME_TIME * 3
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
                enemy.hit(self.manager.get_object("player"), damage = self.damage, kb_magnitude = self.knockback)
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

class FireballSpell(Spell):
    def __init__(self, parent: Player) -> None:
        super().__init__(
            parent,
            icon_key = "items/fireball",
            cooldown_time = 20.0,
        )

        self.damage = 5
        self.knockback = 3
        self.spawn_number = 8
        self.spawn_speed = 7
        self.momentum_coef = 0.5

    def attack(self) -> None:
        super().attack()

        for a in range(self.spawn_number):
            angle = a / self.spawn_number * 360

            self.add_child(FireballProjectile(
                parent = self,
                origin = self.player.rect.center,
                velocity = util.polar_to_cart(angle, self.spawn_speed) + self.player.velocity * self.momentum_coef,
                damage = self.damage,
                knockback = self.knockback,
                max_life = 300,
                rotation_degrees = angle,
                scale = 2,
            ))

class Projectile(Sprite):
    """
    Represents player spawned projectiles which can damage enemies.
    """
    def __init__(self, parent: Node, origin: Vec2, velocity: Vec2, damage: float, knockback: float, image_key: str = "error", max_life: int = 999) -> None:
        super().__init__(parent, groups = ["update", "render"])

        self.image = self.manager.get_image(image_key)
        self.rect = self.image.get_rect(center = origin)

        self.velocity = velocity
        self.life = max_life
        self.damage = damage
        self.knockback = knockback

        self.floor_manager: FloorManager = self.manager.get_object("floor-manager")

    def update(self):
        self.life -= self.manager.dt
        if self.life <= 0:
            # kill with no dying animation
            super().kill()
            return

        self.rect.topleft += self.velocity
        for enemy in self.manager.groups["enemy"]:
            if enemy.rect.colliderect(self):
                enemy.hit(self, damage = self.damage, kb_magnitude = self.knockback)
                self.kill()
                return
            
        current_room = self.floor_manager.get_room_at_world_pos(self.rect.center)
        for tile in current_room.collide_sprites:
            if self.rect.colliderect(tile.rect):
                self.kill()
                return

class FireballProjectile(Projectile):
    def __init__(self, parent: Node, origin: Vec2, velocity: Vec2, damage: float, knockback: float, max_life: int = 999, rotation_degrees: float = 0, scale: int = 1):
        super().__init__(parent, origin, velocity, damage, knockback, max_life)

        self.image = pygame.transform.scale_by(pygame.transform.rotate(self.manager.get_image("items/fireball"), rotation_degrees + 90), scale)
        self.rect = self.image.get_rect(center = origin)