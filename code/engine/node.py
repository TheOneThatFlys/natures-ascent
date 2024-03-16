from __future__ import annotations
import pygame
from .manager import Manager
from typing import TypeVar

T = TypeVar("T", bound = "Node")

class Node():
    def __init__(self, parent: Node):
        self.parent: Node = parent
        self.manager: Manager = parent.manager
        self.children: list[Node] = []

    def update(self) -> None:
        pass

    def add_child(self, child: T) -> T:
        self.children.append(child)
        if hasattr(child, "id"):
            self.manager.add_object(child.id, child)
        return child

    def remove_child(self, child: Node) -> Node:
        self.children.remove(child)
