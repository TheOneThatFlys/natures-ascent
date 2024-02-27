import pygame
from util.constants import *
from entity import Entity

class Player(Entity):
    def __init__(self, parent, start_pos: pygame.Vector2):
        super().__init__(parent)
        self.id = "player"
        self.image = pygame.Surface((TILE_SIZE // 2, TILE_SIZE // 2))
        self.image.fill((49, 222, 49))
        self.rect = self.image.get_rect(topleft = start_pos)
        self.pos.xy = self.rect.topleft

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

        # normalise vector so that diagonal movement is the
        # same speed as horizontal
        if dv.magnitude() != 0:
            dv = dv.normalize() * 1.5

        self.add_velocity(dv)

    def update(self):
        super().update()
        self.get_inputs()
        if self.iframes > 0:
            self.image.fill((0, 0, 255))
        else:
            self.image.fill((49, 222, 49))