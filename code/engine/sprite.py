import pygame
from .node import Node

class Sprite(pygame.sprite.Sprite, Node):
    def __init__(self, parent, groups: list[str] = []):
        Node.__init__(self, parent)
        super().__init__()
        for g in groups:
            self.add(self.manager.groups[g])