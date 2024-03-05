import pygame
from .node import Node

class Sprite(pygame.sprite.Sprite, Node):
    def __init__(self, parent, groups: list[str] = []):
        Node.__init__(self, parent)
        pygame.sprite.Sprite.__init__(self)
        
        for g in groups:
            self.add(self.manager.groups[g])

    def kill(self):
        for child in self.children:
            if isinstance(child, Sprite):
                child.kill()
            
        self.parent.remove_child(self)
        pygame.sprite.Sprite.kill(self)