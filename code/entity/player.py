import pygame
from engine.types import *
from util import parse_spritesheet, scale_surface_by, get_closest_direction
from util.constants import *
from weapon import MeleeWeaponAttack, WeaponStats
from .entity import Entity
from .stats import EntityStats

class LastFacing:
    "Class to store last facing direction data of player."
    def __init__(self):
        self.walk: Direction = "right"
        self.attack: Direction = "right"
        self.overall: Direction = "right"

    def set(self, type: str, direction: Direction):
        self.overall = direction
        if type == "walk":
            self.walk = direction
        elif type == "attack":
            self.attack = direction
        else:
            raise TypeError("Unknown facing type: " + type)

class Player(Entity):
    def __init__(self, parent, start_pos: pygame.Vector2):
        super().__init__(
            parent,
            stats =  EntityStats(
                health = 100,
                walk_speed = 1.5,
                iframes = 60,
            ),
            health_bar_mode = "normal"
        )

        self.id = "player"
        # self.image = pygame.Surface((TILE_SIZE // 2, TILE_SIZE // 2))
        # self.image.fill((49, 222, 49))
        
        self._load_animations()
        self.image = self.animation_manager.set_animation("idle-right")

        self.rect = self.image.get_rect(topleft = start_pos)
        self.pos.xy = self.rect.topleft

        self.health_bar.health_colour = (60, 222, 34)

        self.last_facing = LastFacing()
        self.walking = False

        self.DELETE_LATER_attack_cd = 30
        self.attack_cd = self.DELETE_LATER_attack_cd

    def _load_animations(self):
        types = ["idle", "damage", "walk"]
        directions = ["right", "left", "down", "up"]
        for type in types:
            rows = parse_spritesheet(scale_surface_by(self.manager.get_image("player/" + type), 2), frame_count = 4, direction = "y")
            for i, dir in enumerate(directions):
                anim = parse_spritesheet(rows[i], frame_size = (32 * PIXEL_SCALE, 32 * PIXEL_SCALE))
                self.animation_manager.add_animation(type + "-" + dir, anim)

        attack_rows = parse_spritesheet(scale_surface_by(self.manager.get_image("player/sword_attack"), 2), frame_count = 4, direction = "y")
        for i, dir in enumerate(directions):
            anim = parse_spritesheet(attack_rows[i], frame_size = (32 * PIXEL_SCALE * 3, 32 * PIXEL_SCALE * 3))
            self.animation_manager.add_animation("sword_attack" + "-" + dir, anim)

    def get_inputs(self):
        # movement
        keys = pygame.key.get_pressed()

        dv = pygame.Vector2()

        self.walking = False

        if keys[pygame.K_w]:
            dv.y -= 1
            self.last_facing.set("walk", "up")
            self.walking = True
        if keys[pygame.K_s]:
            dv.y += 1
            self.last_facing.set("walk", "down")
            self.walking = True
        if keys[pygame.K_a]:
            dv.x -= 1
            self.last_facing.set("walk", "left")
            self.walking = True
        if keys[pygame.K_d]:
            dv.x += 1
            self.last_facing.set("walk", "right")
            self.walking = True

        attacking = False
        if keys[pygame.K_RIGHT]:
            attacking = self.try_attack("right")
        elif keys[pygame.K_LEFT]:
            attacking = self.try_attack("left")
        elif keys[pygame.K_UP]:
            attacking = self.try_attack("up")
        elif keys[pygame.K_DOWN]:
            attacking = self.try_attack("down")

        # normalise vector so that diagonal movement is the
        # same speed as horizontal
        if dv.magnitude() != 0:
            dv = dv.normalize() * self.stats.walk_speed

        self.add_velocity(dv)

        current_animation = self.animation_manager.current
        if "death" in current_animation or "damage" in current_animation or "attack" in current_animation: return

        self.eval_anim()

    def eval_anim(self):
        if self.walking:
            # use last attack direction if in attack anim, else use walk direction
            direction = self.last_facing.attack if self.attack_cd > 0 else self.last_facing.walk
            self.animation_manager.set_animation("walk-" + direction)
        else:
            self.animation_manager.set_animation("idle-" + self.last_facing.overall)

    def hit(self, other, damage: int = 0, kb_magnitude: int = 0):
        super().hit(other, damage, kb_magnitude)
        hit_direction = get_closest_direction(pygame.Vector2(other.rect.center) - pygame.Vector2(self.rect.center))
        if not "attack" in self.animation_manager.current: 
            self.animation_manager.set_animation("damage-" + hit_direction)

    def try_attack(self, direction: Direction) -> bool:
        "Attempts an attack, returning True if successful and False if not"
        if self.attack_cd <= 0 and not "player_attack" in self.manager.objects:
            # create attack
            self.add_child(
                MeleeWeaponAttack(
                    self,
                    WeaponStats(
                        size = (self.rect.width / 2, self.rect.height),
                        damage = 5,
                        attack_time = ANIMATION_FRAME_TIME * 3,
                        knockback = 10,
                    ),
                    direction
                )
            )
            self.attack_cd = self.DELETE_LATER_attack_cd
            self.last_facing.set("attack", direction)
            self.animation_manager.set_animation("sword_attack-" + direction)
            return True
        return False
        
    def update(self):
        super().update()
        self.get_inputs()
        self.attack_cd -= self.manager.dt
        if self.attack_cd < 0:
            self.attack_cd = 0

        if "damage" in self.animation_manager.current or "attack" in self.animation_manager.current:
            if self.animation_manager.finished:
                self.eval_anim()