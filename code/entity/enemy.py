from __future__ import annotations

import pygame, random, math

from typing import TYPE_CHECKING, Callable, Type
if TYPE_CHECKING:
    from world import Room

from .entity import Entity
from .stats import EnemyStats, enemy_stats

from engine import Node, Sprite
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

class BossAttack(Sprite):
    def __init__(self, parent: Enemy, attack_time: int = 0):
        super().__init__(parent, ["update"])
        self.parent: Enemy

        self.max_attack_time = attack_time
        self.attack_timer = 0
        self.should_die = False

    def update(self) -> None:
        self.attack_timer += self.manager.dt
        if self.attack_timer >= self.max_attack_time:
            self.should_die = True

class AttackFourBranches(BossAttack):
    LIFETIME = 120
    CHARGEUP = 40

    class LineSegment(Sprite):
        def __init__(self, parent: AttackFourBranches, direction: Direction, size: Vec2) -> None:
            super().__init__(parent, ["render", "update"])
            self.parent: AttackFourBranches
            self.z_index = 10
            self.direction = direction

            self.image = pygame.Surface(size)
            if direction == "up" or direction == "down":
                self.image = pygame.transform.rotate(self.image, 90)
            self.rect = self.image.get_rect()
            self.align_to_parent()

            self.image.fill((0, 0, 255))
            self.image.set_alpha(0)

        def align_to_parent(self):
            boss_rect = self.parent.parent.rect
            if self.direction == "up":
                self.rect.centerx = boss_rect.centerx
                self.rect.bottom = boss_rect.y
            elif self.direction == "down":
                self.rect.centerx = boss_rect.centerx
                self.rect.top = boss_rect.bottom
            elif self.direction == "left":
                self.rect.centery = boss_rect.centery
                self.rect.right = boss_rect.x
            elif self.direction == "right":
                self.rect.centery = boss_rect.centery
                self.rect.x = boss_rect.right

        def update(self) -> None:
            self.align_to_parent()
            if self.parent.attack_timer < AttackFourBranches.CHARGEUP:
                self.image.set_alpha((self.parent.attack_timer / AttackFourBranches.CHARGEUP) * 100)

    def __init__(self, parent: Enemy) -> None:
        super().__init__(parent, attack_time = AttackFourBranches.LIFETIME)
        for d in ("left", "right", "up", "down"):
            self.add_child(AttackFourBranches.LineSegment(self, d, (16, 1024)))

class TreeBoss(Enemy):
    ATTACK_INTERVAL = 300
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, position, enemy_stats["tree_boss"])

        self.animation_manager.add_animation("default", [self.manager.get_image("tiles/wall_tiles")])
        self.image = self.animation_manager.set_animation("default")
        self.rect = self.image.get_frect(center = position)

        self.in_stationary_attack = False

        self.next_attack_timer = 0
        self.in_attack_timer = 0
        self.possible_attacks: list[Type[BossAttack]] = [AttackFourBranches]
        self.current_attack: BossAttack | None = None

    def hit(self, other: Sprite, damage: float = 0, kb_magnitude: float = 0) -> None:
        return super().hit(other, damage, 0 if self.in_stationary_attack else kb_magnitude)

    def update_ai(self) -> None:
        self.follow_player()
        if self.in_stationary_attack:
            self.velocity = pygame.Vector2()

        # if in an attack
        if self.current_attack:
            if self.current_attack.should_die:
                # remove movement lock, queue next event
                self.current_attack.kill()
                self.current_attack = None
                self.in_stationary_attack = False
                self.next_attack_timer = random.randint(self.ATTACK_INTERVAL - 50, self.ATTACK_INTERVAL + 50)
        # count down to next attack
        else:
            self.next_attack_timer -= self.manager.dt
            if self.next_attack_timer <= 0:
                self.current_attack = self.add_child(random.choice(self.possible_attacks)(self))
                self.in_stationary_attack = True

    def update(self) -> None:
        Entity.update(self)
        self.update_ai()
        self.check_player_collision()