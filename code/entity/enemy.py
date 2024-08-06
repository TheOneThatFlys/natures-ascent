from __future__ import annotations

import pygame, random, math

from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from world import Room
    from .player import Player

from .entity import Entity
from .stats import EnemyStats, enemy_stats

from engine import Node, Sprite, AnimationManager
from engine.types import *
from item import Coin
import util
from util.constants import *

class EnemySpawnIndicator(Sprite):
    """
    Sprite that displays the warning indicator for the location of an enemy spawn.

    Will call parent.place_in_world on death after 1 second.
    """
    def __init__(self, parent: Enemy) -> None:
        super().__init__(parent, ["render", "update"], 0)
        self.animation_manager = self.add_child(AnimationManager(parent = self))
        self.animation_manager.add_animation("default", util.parse_spritesheet(pygame.transform.scale_by(self.manager.get_image("tiles/spawn_warning"), 2), frame_size=(TILE_SIZE, TILE_SIZE)))
        self.image = self.animation_manager.set_animation("default")
        self.rect = self.image.get_rect(topleft = parent.rect.topleft)

        self.counter = 0
        self.life_time = 60 + random.randint(0, 30)

    def update(self) -> None:
        self.animation_manager.update()
        self.counter += self.manager.dt
        if self.counter >= self.life_time: # TEMP
            self.kill()

    def kill(self) -> None:
        self.parent.place_in_world()
        super().kill()

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
        
        self.remove(self.manager.groups["update"])
        self.remove(self.manager.groups["render"])

        self.animation_manager.add_animation("__TEMP", [self.manager.get_image("error")])
        self.image = self.animation_manager.set_animation("__TEMP")

        self.rect = self.image.get_frect(topleft = position)

        # some useful info for subclasses
        self.time_since_seen_player = math.inf
        self.has_seen_player = False

        self.player = self.manager.get_object("player")

        # spawn in animation
        self.spawn_time = 60
        self.spawn_counter = 0

        self.spawn_indicator = self.add_child(EnemySpawnIndicator(parent = self))
        self.falling_in = True

    def place_in_world(self) -> None:
        self.add(self.manager.groups["render"])
        self.add(self.manager.groups["update"])
        self.add(self.manager.groups["enemy"])

        screen_height = self.manager.get_window("main").size[1]
        self.target_y = self.rect.y # keep track of original spawn location
        self.rect.y -= screen_height # move entity out of screen view
        self.fall_speed = screen_height / 60 # move linearly down for 1 second

        self.z_index = 10 # make sure enemy is rendered on top of everything else in world

    def move(self):
        """Enemy can override move to use a better form of collision as enemies will not be able to leave their rooms"""
        check_tile_collisions = not self.parent.inside_rect.contains(self.rect)
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
        
        # for blocking_sprite in self.parent.collide_sprites:
        #     if blocking_sprite.rect.clipline(self.rect.center, target_position):
        #         return False
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

    def calculate_damage_frames(self) -> None:
        """Draw a red overlay over enemy sprite when taking damage"""
        if self.iframes > 0:
            alpha = (self.iframes / self.stats.iframes) * 122

            self.image = self.animation_manager.get_current_frame().copy()
            mask = pygame.mask.from_surface(self.image)
            mask = mask.to_surface(setcolor=(255, 0, 0), unsetcolor=None)
            mask.set_alpha(alpha)
            self.image.blit(mask, (0, 0))

    def update(self) -> None:
        if self.falling_in:
            self.rect.y += self.fall_speed
            if self.rect.y > self.target_y:
                self.rect.y = self.target_y
                self.falling_in = False # stop falling animation
                self.z_index = 0 # reset z index
                self.manager.play_sound(self.stats.enter_sound, volume=0.2)
            return

        self.time_since_seen_player += self.manager.dt
        if self.has_line_of_sight(self.player.rect.center):
            self.time_since_seen_player = 0

        self.update_ai()
        self.avoid_others()
        self.check_player_collision()

        super().update()

        self.calculate_damage_frames()

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
            animation_key = util.get_closest_direction(pygame.Vector2(self.player.rect.center) - self.rect.center)
            if animation_key != self.animation_manager.current:
                self.animation_manager.set_animation(animation_key)

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
        def __init__(self, parent: AttackFourBranches, direction: Direction, short: int, long: int) -> None:
            super().__init__(parent, ["render", "update"])
            self.parent: AttackFourBranches

            self.direction = direction
            self.size = (long, short) if direction == "left" or direction == "right" else (short, long)
            self.short, self.long = short, long

            self.grow_vector = pygame.Vector2(1, 0) if direction == "left" or direction == "right" else pygame.Vector2(0, 1)
            self.image = pygame.Surface(self.size)
            self.rect = self.image.get_frect()
            self.align_to_parent()

            self.image.fill((0, 0, 255))
            self.image.set_alpha(0)

            self.z_index = 10

            self.player = self.manager.get_object("player")

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
            if self.parent.attack_timer < AttackFourBranches.CHARGEUP:
                self.image.set_alpha((self.parent.attack_timer / AttackFourBranches.CHARGEUP) * 100)
            else:
                new_length = (self.parent.attack_timer - AttackFourBranches.CHARGEUP) / (self.parent.max_attack_time - AttackFourBranches.CHARGEUP) * self.long
                self.image = pygame.Surface((self.short, self.short) + self.grow_vector * (new_length))
                self.rect = self.image.get_frect()
                self.align_to_parent()
                
                if self.rect.colliderect(self.player.rect):
                    self.player.hit(self, 10)

    def __init__(self, parent: Enemy) -> None:
        super().__init__(parent, attack_time = AttackFourBranches.LIFETIME)
        for d in ("left", "right", "up", "down"):
            self.add_child(AttackFourBranches.LineSegment(self, d, 64, 1024))

class Attack8Projectiles(BossAttack):
    CHARGEUP = 10
    LIFE = 120
    
    class Projectile(Sprite):
        def __init__(self, parent: Attack8Projectiles, direction: pygame.Vector2) -> None:
            super().__init__(parent, ["render", "update"])
            self.velocity = direction.normalize() * 5
            self.image = pygame.Surface((32, 32))
            self.rect = self.image.get_rect(center = parent.rect.center)
            self.life = Attack8Projectiles.LIFE

        def update(self):
            self.rect.topleft += self.velocity * self.manager.dt
            self.life -= self.manager.dt
            if self.life <= 0:
                self.kill()

    def __init__(self, parent: Enemy) -> None:
        super().__init__(parent, attack_time = 20)
        self.chargeup_timer = 0
        self.attacked = False

    def update(self):
        super().update()
        if self.attacked: return
        self.chargeup_timer += self.manager.dt
        if self.chargeup_timer >= Attack8Projectiles.CHARGEUP:
            self.attack()
            self.attacked = True

    def attack(self):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0: continue
                self.parent.add_child(Attack8Projectiles.Projectile(self.parent, pygame.Vector2(dx, dy)))

class TreeBoss(Enemy):
    ATTACK_INTERVAL = 300
    def __init__(self, parent: Node, position: Vec2) -> None:
        super().__init__(parent, position, enemy_stats["tree_boss"])
        rows = util.parse_spritesheet(pygame.transform.scale_by(self.manager.get_image("enemy/slime_green"), 8), frame_count = 4, direction = "y")
        directions = ["down", "right", "up", "left"]
        for i, dir in enumerate(directions):
            self.animation_manager.add_animation(dir, util.parse_spritesheet(rows[i], frame_count = 2))

        self.image = self.animation_manager.set_animation("down")
        self.rect = self.image.get_frect(center = position)

        self.in_stationary_attack = False

        self.next_attack_timer = self.ATTACK_INTERVAL
        self.in_attack_timer = 0
        self.possible_attacks: list[Type[BossAttack]] = [Attack8Projectiles, AttackFourBranches]
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
        super().update()
        self.animation_manager.set_animation(util.get_closest_direction(pygame.Vector2(self.player.rect.center) - self.rect.center))