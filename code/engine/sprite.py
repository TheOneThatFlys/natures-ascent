import pygame
from .node import Node

class Sprite(pygame.sprite.Sprite, Node):
    def __init__(self, parent: Node, groups: list[str] = [], z_index: int = 0) -> None:
        Node.__init__(self, parent)
        pygame.sprite.Sprite.__init__(self)

        self.render_offset = (0, 0)
        self.z_index = z_index
        
        for g in groups:
            self.add(self.manager.groups[g])

    def kill(self) -> None:
        # create shallow copy of list because it breaks without
        # for some god forsaken reason
        for child in self.children[:]:
            if isinstance(child, Sprite):
                child.kill()
            
        self.parent.remove_child(self)
        pygame.sprite.Sprite.kill(self)
        if hasattr(self, "id"):
            self.manager.remove_object(self.id)