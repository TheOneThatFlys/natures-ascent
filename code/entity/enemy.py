import pygame, math
from entity import Entity
from util.math import clamp

class Enemy(Entity):
    def __init__(self, parent, start_pos):
        super().__init__(parent)
        self.image = pygame.Surface((32, 32))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft = start_pos)
        self.pos.xy = self.rect.topleft

        self.player = self.manager.get_object_from_id("player")

    def follow_player(self):
        if (pygame.Vector2(self.rect.center) - pygame.Vector2(self.player.rect.center)).magnitude() < 12: return

        velocity = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
        if velocity.magnitude() != 0:
            velocity = velocity.normalize() * 0.6

        self.add_velocity(velocity)

    def check_player_collision(self):
        if self.rect.colliderect(self.player.rect):
            self.player.hit(self, kb_magnitude = 10)

    def update(self):
        self.follow_player()
        self.check_player_collision()
        super().update()