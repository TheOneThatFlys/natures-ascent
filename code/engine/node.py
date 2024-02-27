from __future__ import annotations
import pygame
from .manager import Manager

class Node():
    def __init__(self, parent: Node):
        self.parent: Node = parent
        self.manager: Manager = parent.manager
        self.children: list[Node] = []

    def update(self) -> None:
        pass

    def get_render_offset(self) -> pygame.Vector2:
        return pygame.Vector2(0, 0)

    def add_child(self, child: Node) -> Node:
        self.children.append(child)
        if hasattr(child, "id"):
            self.manager.add_object(child.id, child)
        return child

    def remove_child(self, child: Node) -> Node:
        self.children.remove(child)
