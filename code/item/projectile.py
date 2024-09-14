from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from world import FloorManager
    from entity import Entity

import pygame, math

from engine import Sprite, Node, AnimationManager
from engine.types import Vec2

class Projectile(Sprite):
    """
    Represents spawned projectiles which can damage specified entities.\n
    If the projectile has a pierce value, it will continue to travel after hitting `n` enemies.\n
    If adjust_rotation is `True`, the projectile will rotate to face its direction of travel, assuming the original is facing right.
    """
    def __init__(
            self,
            parent: Node,
            origin: Vec2,
            velocity: Vec2,
            damage: float,
            enemy_group: pygame.sprite.Group,
            knockback: float = 0.0,
            hitbox_size: int = -1,
            image_key: str = "error",
            max_life: int = 999,
            pierce: int = 0,
            adjust_rotation: bool = True
        ) -> None:

        super().__init__(parent, groups = ["update", "render"])
        self.animation_manager = self.add_child(AnimationManager(self))
        self.animation_manager.add_animation("still", [self.manager.get_image(image_key)])
        if adjust_rotation: self.animation_manager.rotate_animation("still", -math.degrees(math.atan2(velocity[1], velocity[0])))
        self.image = self.animation_manager.set_animation("still")

        self.rect = self.image.get_rect(center = origin)
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size) if hitbox_size > 0 else self.rect
        self.z_index = 1

        self.hitbox.center = self.rect.center

        self.enemy_group = enemy_group

        self.velocity = velocity
        self.life = max_life
        self.damage = damage
        self.knockback = knockback

        self.pierce = pierce

        self.floor_manager: FloorManager = self.manager.get_object("floor-manager")

    def update(self):
        self.animation_manager.update()
        self.life -= self.manager.dt
        if self.life <= 0:
            # kill with no dying animation
            super().kill()
            return

        self.rect.topleft += self.velocity * self.manager.dt
        self.hitbox.center = self.rect.center
        for enemy in self.enemy_group:
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