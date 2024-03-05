import pygame
from util.constants import *
from weapon import MeleeWeaponAttack, WeaponStats
from engine import parse_animation, AnimationManager
from .entity import Entity
from .stats import EntityStats

class Player(Entity):
    def __init__(self, parent, start_pos: pygame.Vector2):
        super().__init__(
            parent,
            stats =  EntityStats(
                health = 100,
                walk_speed = 1.5,
                iframes = 60,
            ),
            hide_health_bar = True
        )

        self.id = "player"
        # self.image = pygame.Surface((TILE_SIZE // 2, TILE_SIZE // 2))
        # self.image.fill((49, 222, 49))
        self.animation_manager = self.add_child(AnimationManager(self))
        self.animation_manager.add_animation("idle", parse_animation(self.manager.get_image("TEMP_PLAYER"), frame_count = 4))
        self.animation_manager.set_animation("idle")
        self.image = self.animation_manager.get_default("idle")

        self.rect = self.image.get_rect(topleft = start_pos)
        self.pos.xy = self.rect.topleft

        self.DELETE_LATER_attack_cd = 30
        self.attack_cd = self.DELETE_LATER_attack_cd

    def get_inputs(self):
        # movement
        keys = pygame.key.get_pressed()

        dv = pygame.Vector2()

        if keys[pygame.K_w]:
            dv.y -= 1
        if keys[pygame.K_s]:
            dv.y += 1
        if keys[pygame.K_a]:
            dv.x -= 1
        if keys[pygame.K_d]:
            dv.x += 1

        if keys[pygame.K_RIGHT]:
            self.try_attack("right")
        elif keys[pygame.K_LEFT]:
            self.try_attack("left")
        elif keys[pygame.K_UP]:
            self.try_attack("up")
        elif keys[pygame.K_DOWN]:
            self.try_attack("down")

        # normalise vector so that diagonal movement is the
        # same speed as horizontal
        if dv.magnitude() != 0:
            dv = dv.normalize() * self.stats.walk_speed

        self.add_velocity(dv)

    def try_attack(self, direction):
        if self.attack_cd <= 0:
            temp_s = pygame.Surface((32, 64))
            temp_s.fill((255, 255, 0))
            # create attack
            self.add_child(
                MeleeWeaponAttack(
                    self,
                    temp_s,
                    WeaponStats(
                        size = (32, 64),
                        damage = 5,
                        attack_time = 30,
                        knockback = 10,
                    ),
                    direction
                )
            )
            self.attack_cd = self.DELETE_LATER_attack_cd

    def update(self):
        super().update()
        self.get_inputs()
        self.animation_manager.update()
        self.attack_cd -= self.manager.dt
        if self.attack_cd < 0:
            self.attack_cd = 0

        # if self.iframes > 0:
        #     self.image.fill((0, 0, 255))
        # else:
        #     self.image.fill((49, 222, 49))