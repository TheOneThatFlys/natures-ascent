import pygame

from .node import Node

from .types import *
from .ui import Element, Style

class Screen(Node):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.rect = parent.window.get_surface().get_rect()
        self.master_container = self.add_child(Element(parent = self, style = Style(size = self.rect.size, alpha = 0)))
        
    def on_key_down(self, key: int, unicode: str) -> None:
        """Called when a keyboard key is pressed."""
        self.master_container.on_key_down(key, unicode)

    def on_mouse_down(self, button: int) -> None:
        """
        Called when a mouse button is pressed.
        - 1 = left click
        - 2 = scroll wheel click
        - 3 = right click
        """
        self.master_container.on_mouse_down(button)

    def on_mouse_up(self, button: int) -> None:
        """Called when mouse button is released. See ``Screen.on_mouse_down``"""
        self.master_container.on_mouse_up(button)

    def on_scroll(self, dx: int, dy: int) -> None:
        """Called when mouse wheel is scrolled. Supports both horizontal and vertical scrolling."""
        self.master_container.on_scroll(dx, dy)

    def on_resize(self, new_res: Vec2) -> None:
        """Called when the window is resized, either by dragging the window or changing the window mode."""
        self.rect.size = new_res
        self.master_container.style.size = new_res
        self.master_container.redraw_image()
        self.master_container.on_resize(new_res)

    def kill(self) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass