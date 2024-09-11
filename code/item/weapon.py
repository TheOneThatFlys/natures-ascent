from __future__ import annotations
from typing import Type, TYPE_CHECKING, TypeVar
if TYPE_CHECKING:
    from entity import Player
    from world import FloorManager

import pygame

from engine import Sprite, Node, Logger
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
        try:
            self.player: Player = self.manager.get_object("player")
        except KeyError:
            self.player = parent

        self.animation_key = animation_key
        self.sound_key = sound_key
        self.icon_key = icon_key
        self.cooldown_time = cooldown_time

        self.upgrade_level = 0

    def attack(self, direction: Direction) -> None:
        if self.sound_key:
            self.manager.play_sound(self.sound_key, volume=0.2)

    def upgrade(self) -> None:
        if self.upgrade_level == 3: return
        self.upgrade_level += 1
        match self.upgrade_level:
            case 1: self.upgrade_1()
            case 2: self.upgrade_2()
            case 3: self.upgrade_3()
            case _: None

    def upgrade_1(self) -> None:
        """Called when first upgrade is applied. Example use: ``self.damage += 10``"""

    def upgrade_2(self) -> None:
        """See ``upgrade_1``"""

    def upgrade_3(self) -> None:
        """See ``upgrade_1``"""

class Spell(Weapon):
    """
    Same as a weapon, but attack direction does not matter (as it is binded to a single key)
    """
    def attack(self) -> None:
        super().attack(None)

class MeleeWeaponAttack(Sprite):
    def __init__(self, parent: Player, direction: Direction, damage: float, knockback: float, width: float, length: float, hit_frames: list[tuple[int, int]], total_life: int) -> None:
        super().__init__(parent, groups = ["update"])
        self.z_index = 1
        self.direction = direction
        self.damage = damage
        self.knockback = knockback

        self.life = total_life
        self.rect = pygame.Rect(0, 0, length, width)
        self.hit_frames = hit_frames
        self.frames_alive = 0
        self._hit_enemies = [] # keep track of hit enemies

        # flip hitbox if attacking up or down 
        if direction == "up" or direction == "down":
            self.rect.width, self.rect.height = self.rect.height, self.rect.width

        self.direction = direction

        self._stick_to_parent_position()

    def _check_enemy_collisions(self) -> None:
        # check if hitting enemy
        for enemy in self.manager.groups["enemy"].sprites():
            if self.rect.colliderect(enemy.hitbox) and not enemy in self._hit_enemies:
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

    def in_hit_frames(self) -> bool:
        for frame_range in self.hit_frames:
            if frame_range[0] < self.frames_alive < frame_range[1]:
                return True
        return False

    def update(self) -> None:
        self._stick_to_parent_position()
        if self.in_hit_frames():
            self._check_enemy_collisions()
        self.life -= self.manager.dt
        self.frames_alive += self.manager.dt
        if self.life < 0:
            self.kill()

class Projectile(Sprite):
    """
    Represents player spawned projectiles which can damage enemies.
    """
    def __init__(self, parent: Node, origin: Vec2, velocity: Vec2, damage: float, knockback: float, hitbox_size: int = -1, image_key: str = "error", max_life: int = 999, pierce: int = 0) -> None:
        super().__init__(parent, groups = ["update", "render"])
        self.z_index = 1
        self.image = self.manager.get_image(image_key)
        self.rect = self.image.get_rect(center = origin)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size) if hitbox_size > 0 else self.rect

        self.hitbox.center = self.rect.center

        self.velocity = velocity
        self.life = max_life
        self.damage = damage
        self.knockback = knockback

        self.pierce = pierce

        self.floor_manager: FloorManager = self.manager.get_object("floor-manager")

    def update(self):
        self.life -= self.manager.dt
        if self.life <= 0:
            # kill with no dying animation
            super().kill()
            return

        self.rect.topleft += self.velocity * self.manager.dt
        self.hitbox.center = self.rect.center
        for enemy in self.manager.groups["enemy"]:
            if enemy.hitbox.colliderect(self.hitbox):
                success = enemy.hit(self, damage = self.damage, kb_magnitude = self.knockback)
                if success: self.pierce -= 1
                if self.pierce < 0:
                    self.kill()
                return
            
        current_room = self.floor_manager.get_room_at_world_pos(self.rect.center)
        for tile in current_room.collide_sprites.sprites() + current_room.temp_doors.sprites():
            if self.hitbox.colliderect(tile.rect):
                self.kill()
                return
            
class Sword(Weapon):
    def __init__(self, parent: Player) -> None:
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
        self.player.add_child(MeleeWeaponAttack(
            parent = self.player,
            direction = direction,
            damage = self.damage,
            knockback = self.knockback,
            width = 64, length = 48,
            total_life = ANIMATION_FRAME_TIME * 4,
            hit_frames = [(ANIMATION_FRAME_TIME, ANIMATION_FRAME_TIME * 2)]
        ))

        if self.upgrade_level == 3:
            self.add_child(SwordProjectile(
                parent = self,
                origin = self.player.rect.center,
                velocity = pygame.Vector2(util.get_direction_vector(direction)) * 5,
                rotation = util.get_direction_angle(direction),
                damage = 5,
                spawn_delay = ANIMATION_FRAME_TIME
            ))

    def upgrade_1(self) -> None:
        self.damage = 15

    def upgrade_2(self) -> None:
        self.cooldown_time = 30

class SwordProjectile(Projectile):
    def __init__(self, parent: Node, origin: Vec2, velocity: Vec2, rotation: float, damage: float, spawn_delay: int = 0) -> None:
        super().__init__(
            parent = parent,
            origin = origin,
            velocity = velocity,
            damage = damage,
            knockback = 0,
            image_key = "items/sword_proj",
            hitbox_size = 12,
            pierce = 999
        )

        self.image = pygame.transform.rotate(self.image, rotation)
        if rotation % 180 == 90: self.rect.width, self.rect.height = self.rect.height, self.rect.width

        self.spawn_delay = spawn_delay
        self.spawned = False

        self.remove(self.manager.groups["render"])

    def update(self) -> None:
        if not self.spawned:
            self.spawn_delay -= self.manager.dt
            if self.spawn_delay < 0:
                self.spawned = True
                self.add(self.manager.groups["render"])
                player = self.manager.get_object("player")
                self.rect.center = player.rect.center
                self.velocity += player.velocity * 0.5
        else:
            super().update()

class Spear(Weapon):
    def __init__(self, parent: Player) -> None:
        super().__init__(
            parent,
            cooldown_time = ANIMATION_FRAME_TIME * 4,
            animation_key = "spear_attack",
            icon_key = "items/spear",
            sound_key = "effect/spear_swoosh"
        )

        self.damage = 10.0
        self.knockback = 15.0

    def attack(self, direction: Direction) -> None:
        super().attack(direction)
        self.player.add_child(MeleeWeaponAttack(
            parent = self.player,
            direction = direction,
            damage = self.damage,
            knockback = self.knockback,
            width = 32,
            length = 64,
            total_life = ANIMATION_FRAME_TIME * 3,
            hit_frames = [(ANIMATION_FRAME_TIME, ANIMATION_FRAME_TIME * 2)]
        ))

class FireballSpell(Spell):
    def __init__(self, parent: Player) -> None:
        super().__init__(
            parent,
            icon_key = "items/fireball",
            cooldown_time = 90.0,
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
                scale = 1,
            ))

class FireballProjectile(Projectile):
    def __init__(self, parent: Node, origin: Vec2, velocity: Vec2, damage: float, knockback: float, max_life: int = 999, rotation_degrees: float = 0, scale: int = 1):
        super().__init__(
            parent=parent,
            origin=origin,
            velocity=velocity,
            damage=damage,
            knockback=knockback,
            hitbox_size=16 * scale,
            max_life=max_life
        )

        self.image = pygame.transform.scale_by(pygame.transform.rotate(self.manager.get_image("items/fireball"), rotation_degrees + 90), scale)
        self.rect = self.image.get_rect(center = origin)

class DashSpell(Spell):
    # terrible hack to get a timer to update
    class __FrictionNormaliser(Sprite):
        def __init__(self, parent: Node) -> None:
            super().__init__(parent, ["update"])
            self.counter = 0

        def update(self) -> None:
            self.counter += self.manager.dt
            if self.counter > 10:
                player: Player = self.manager.get_object("player")
                player.local_friction_coef = SURFACE_FRICTION_COEFFICIENT
                player.disable_movement_input = False
                self.kill()

    def __init__(self, parent: Player) -> None:
        super().__init__(
            parent,
            cooldown_time = 45,
            sound_key = "effect/dash",
            icon_key = "items/dash"
        )

        if self.cooldown_time < 16:
            Logger.warn(f"Dash spell cooldown set to {self.cooldown_time}, which is below the recommended minimum of {16}.")

        self.magnitude = 10

        self.dash_timer = 0

    def attack(self) -> None:
        super().attack()
        direction = pygame.Vector2()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_d]: direction.x += 1
        if keys[pygame.K_a]: direction.x -= 1
        if keys[pygame.K_w]: direction.y -= 1
        if keys[pygame.K_s]: direction.y += 1

        # default to facing if no input pressed
        if direction.magnitude() == 0:
            last_direction = self.player.last_facing.overall
            direction = pygame.Vector2(util.get_direction_vector(last_direction))
        self.player.velocity = direction.normalize() * self.magnitude
        self.player.iframes = 16
        self.player.local_friction_coef = 0
        self.player.disable_movement_input = True
        self.add_child(DashSpell.__FrictionNormaliser(self))
        self.player.animation_manager.set_animation("dash-" + self.player.last_facing.overall)
        cam = self.manager.get_object("camera")
        cam.shake(2, 5)

Item = Weapon|Spell
class ItemPool(Node):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.id = "itempool"

        # store items for id tracking
        self.items = [
            Sword, Spear,
            FireballSpell, DashSpell,
        ]

        self.weights = {
            Spear: 1,
            FireballSpell: 1,
            DashSpell: 1,
        }

        self.found_items: list[int] = []
    
    def get_item_id(self, t: Item|Type[Item]|None) -> int:
        if t == None: return -1
        if not isinstance(t, Type): t = type(t)
        return self.items.index(t)

    def get_item(self, id: int) -> Type[Item]:
        return self.items[id]

    def roll(self) -> Type[Item]:
        a = util.choose_weighted(self.weights)
        self.found_items.append(self.get_item_id(a))
        del self.weights[a]
        return a
    
    def restore_from_found(self, found: list[int]) -> None:
        self.found_items = found
        for item_id in found:
            del self.weights[self.get_item(item_id)]
        
    def is_empty(self) -> None:
        return not self.weights
        