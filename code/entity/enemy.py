from __future__ import annotations

import pygame, random, math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from world import Room

from .entity import Entity
from .stats import EnemyStats, enemy_stats

from engine import Node
from engine.types import *
from item import Coin
import util

class Enemy(Entity):
    """
    Class to represent enemies.
    
    Stats are provided through Enemy.stats, and custom ai can be implemented by overriding Enemy.update_ai().
    """
    def __init__(self, parent: Room, position: Vec2, stats: EnemyStats) -> None:
        super().__init__(
            parent,
            stats = stats
        )
        self.stats: EnemyStats
        self.parent: Room
        
        self.add(self.manager.groups["enemy"])
        self.remove(self.manager.groups["update"])

        self.animation_manager.add_animation("__TEMP", [self.manager.get_image("error")])
        self.image = self.animation_manager.set_animation("__TEMP")

        self.rect = self.image.get_frect(topleft = position)

        # some useful info for subclasses
        self.time_since_seen_player = math.inf
        self.has_seen_player = False

        self.player = self.manager.get_object("player")

    def move(self):
        """Enemy can override move to use a better form of collision as enemies will not be able to leave their rooms"""
        check_tile_collisions = self.parent.inside_rect.contains(self.rect)
        self.rect.x += self.velocity.x * self.manager.dt
        if check_tile_collisions: self.check_collision_horizontal(collide_group = self.parent.collide_sprites)
        self.rect.y += self.velocity.y * self.manager.dt
        if check_tile_collisions: self.check_collision_vertical(collide_group = self.parent.collide_sprites)

        # constrain self within parent room
        bounds: pygame.Rect = self.parent.bounding_rect
        if self.rect.left < bounds.left:
            self.rect.left = bounds.left
        elif self.rect.right > bounds.right:
            self.rect.right = bounds.right
        if self.rect.top < bounds.top:
            self.rect.top = bounds.top
        elif self.rect.bottom > bounds.bottom:
            self.rect.bottom = bounds.bottom

        self.apply_friction()

    def follow_player(self) -> None:
        if (pygame.Vector2(self.rect.center) - pygame.Vector2(self.player.rect.center)).magnitude() < 12: return

        velocity = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
        if velocity.magnitude() != 0:
            velocity = velocity.normalize() * self.stats.walk_speed

        self.add_velocity(velocity)

    def has_line_of_sight(self, target_position: Vec2) -> bool:
        if (pygame.Vector2(target_position) - self.rect.center).magnitude() > self.stats.notice_range:
            return False
        
        for blocking_sprite in self.parent.collide_sprites:
            if blocking_sprite.rect.clipline(self.rect.center, target_position):
                return False
        return True

    def check_player_collision(self) -> None:
        if self.rect.colliderect(self.player.rect):
            self.player.hit(self, kb_magnitude = 10, damage = self.stats.contact_damage)

    def avoid_others(self) -> None:
        for enemy in self.parent.enemies:
            if enemy == self: continue
            if self.rect.colliderect(enemy.rect):
                dv = (self.rect.center - pygame.Vector2(enemy.rect.center)) / 30
                self.add_velocity(dv)

    def kill(self) -> None:
        self.manager.play_sound(sound_name = "effect/squelch", volume = 0.5)
        level = self.manager.get_object("level")
        # add coins
        for _ in range(self.stats.value):
            level.add_child(Coin(level, (self.rect.centerx, self.rect.bottom)))
        super().kill()

    def update_ai(self) -> None:
        """
        Override this function to add custom behaviour to subclass.

        Default behaviour is slime ai: follow player if line of sight
        """
        if self.time_since_seen_player <= self.stats.attention_span:
            self.follow_player()

    def update(self) -> None:
        self.time_since_seen_player += self.manager.dt
        if self.has_line_of_sight(self.player.rect.center):
            self.time_since_seen_player = 0

        self.update_ai()
        self.avoid_others()
        self.check_player_collision()
        
        super().update()

class Slime(Enemy):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, position, enemy_stats["slime"])

        rows = util.parse_spritesheet(pygame.transform.scale_by(self.manager.get_image("enemy/slime_green"), 2), frame_count = 4, direction = "y")
        directions = ["down", "right", "up", "left"]
        for i, dir in enumerate(directions):
            self.animation_manager.add_animation(dir, util.parse_spritesheet(rows[i], frame_count = 2))
        
        self.image = self.animation_manager.set_animation(random.choice(directions))
        self.rect = self.image.get_frect(topleft = position)

    def update(self) -> None:
        super().update()

        if self.time_since_seen_player <= self.stats.attention_span:
            self.animation_manager.set_animation(util.get_closest_direction(pygame.Vector2(self.player.rect.center) - self.rect.center))

class TreeBoss(Enemy):
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, position, enemy_stats["tree_boss"])

        self.image = pygame.Surface((100, 100))
        self.rect = self.image.get_frect(center = position)

    def update_ai(self) -> None:
        self.follow_player()

    def update(self) -> None:
        self.update_ai()
        self.check_player_collision()
        Entity.update(self)