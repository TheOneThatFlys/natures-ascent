import pygame
from engine import Sprite, Node
from engine.types import *
from util.constants import *

class HealthBar(Sprite):

    HEALTH_BAR_WIDTH = TILE_SIZE
    HEALTH_BAR_HEIGHT = 8

    def __init__(self, parent: Node, border_colour: Colour, border_size: int, health_colour: Colour) -> None:
        super().__init__(parent, ["render", "update"])

        self.border_colour = border_colour
        self.border_size = border_size
        self.health_colour = health_colour

        self.hidden = False

        self._redraw_image()

    def _redraw_image(self) -> None:
        max_health = self.parent.stats.health
        current_health = self.parent.health

        self.image = pygame.Surface((
            self.HEALTH_BAR_WIDTH,
            self.HEALTH_BAR_HEIGHT
        ))

        self.image.fill(self.border_colour)
        
        health_rect = pygame.Rect(
            self.border_size,
            self.border_size,
            (current_health / max_health) * (self.HEALTH_BAR_WIDTH - self.border_size * 2),
            self.HEALTH_BAR_HEIGHT - self.border_size * 2
            )

        pygame.draw.rect(self.image, self.health_colour, health_rect)

        self.rect = self.image.get_rect()

    def update(self) -> None:
        self._redraw_image()
        # render bar below parent with a little padding
        self.rect.bottom = self.parent.rect.top - 16
        self.rect.centerx = self.parent.rect.centerx

    def show(self) -> None:
        if self.hidden:
            self.add(self.manager.groups["render"])
            self.hidden = False

    def hide(self) -> None:
        if not self.hidden:
            self.remove(self.manager.groups["render"])
            self.hidden = True
