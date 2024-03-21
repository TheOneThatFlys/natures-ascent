import pygame, random

from .entity import Entity
from .stats import EntityStats

from item import Coin

class Enemy(Entity):
    def __init__(self, parent, start_pos):
        super().__init__(
            parent,
            stats = EntityStats(
                health = 20,
                iframes = 20,
                contact_damage = 10,
                walk_speed = 0.6
            )
        )
        
        self.add(self.manager.groups["enemy"])

        temp_s = pygame.Surface((32, 32))
        temp_s.fill((255, 0, 0))
        self.animation_manager.add_animation("TEMP", [temp_s])
        self.image = self.animation_manager.set_animation("TEMP")

        self.rect = self.image.get_rect(topleft = start_pos)
        self.pos.xy = self.rect.topleft

        self.player = self.manager.get_object_from_id("player")

    def follow_player(self):
        if (pygame.Vector2(self.rect.center) - pygame.Vector2(self.player.rect.center)).magnitude() < 12: return

        velocity = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
        if velocity.magnitude() != 0:
            velocity = velocity.normalize() * self.stats.walk_speed

        self.add_velocity(velocity)

    def check_player_collision(self):
        if self.rect.colliderect(self.player.rect):
            self.player.hit(self, kb_magnitude = 10, damage = self.stats.contact_damage)

    def kill(self):
        self.manager.play_sound(sound_name = "effect/squelch", volume = 0.5)
        level = self.manager.get_object_from_id("level")
        for _ in range(3):
            level.add_child(Coin(level, (self.rect.centerx, self.rect.bottom)))
        super().kill()

    def update(self):
        self.follow_player()
        self.check_player_collision()
        super().update()