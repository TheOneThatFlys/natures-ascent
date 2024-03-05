import pygame
from engine import Sprite
from engine.types import *

class HealthBar(Sprite):

    HEALTH_PIXEL_RATIO = 1

    def __init__(self, parent, border_colour: Colour, border_size: int, health_colour: Colour, health_height: int):
        super().__init__(parent, ["render", "update"])

        self.border_colour = border_colour
        self.border_size = border_size
        self.health_colour = health_colour
        self.health_height = health_height

        self.hidden = False

        self._redraw_image()

    def _redraw_image(self, *padding_xy):
        max_health = self.parent.stats.health
        current_health = self.parent.health

        self.image = pygame.Surface((
            max_health * self.HEALTH_PIXEL_RATIO + self.border_size * 2,
            self.health_height + self.border_size * 2
        ))

        self.image.fill(self.border_colour)
        
        health_rect = pygame.Rect(self.border_size, self.border_size, current_health, self.health_height)
        pygame.draw.rect(self.image, self.health_colour, health_rect)

        self.rect = self.image.get_rect()

    def update(self):
        self._redraw_image()
        # render bar below parent with a little padding
        self.rect.bottom = self.parent.rect.top - 16
        self.rect.centerx = self.parent.rect.centerx

    def show(self):
        if self.hidden:
            print("asdhOISADHOID")
            self.add(self.manager.groups["render"])
            self.hidden = False

    def hide(self):
        if not self.hidden:
            self.remove(self.manager.groups["render"])
            self.hidden = True
