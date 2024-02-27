import pygame
from engine import Sprite

class Tile(Sprite):
    def __init__(self, parent, image, pos):
        super().__init__(parent = parent, groups=["render", "collide"])
        self.image = image
        self.rect = self.image.get_rect(topleft = pos)