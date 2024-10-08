from __future__ import annotations
from .manager import Manager
from typing import TypeVar

from .types import *

T = TypeVar("T", bound = "Node")

class Node(DebugExpandable):
    def __init__(self, parent: Node) -> None:
        self.parent: Node = parent
        self.manager: Manager = parent.manager
        self.children: list[Node] = []

    def update(self) -> None:
        pass

    def add_child(self, child: T) -> T:
        if child.parent != self:
            raise TypeError(f"Type mismatch: child must be initialised with correct parent ({self} : {child.parent})")
        
        self.children.append(child)
        if hasattr(child, "id"):
            self.manager.add_object(child.id, child)
        return child

    def remove_child(self, child: Node) -> Node:
        self.children.remove(child)

    def transfer(self, new_parent: Node) -> Node:
        """Transfer a node to a new parent"""
        if self in self.parent.children: self.parent.remove_child(self)
        self.parent = new_parent
        new_parent.add_child(self)

    def get_all_children(self) -> list[Node]:
        """Recursively traverse through all the children of a node, similar to os.walk"""
        lst = [self]
        for child in self.children:
            lst += child.get_all_children()
        return lst