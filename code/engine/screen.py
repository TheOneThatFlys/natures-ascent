import pygame

from .node import Node

from .types import *

class Screen(Node):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.rect = parent.window.get_surface().get_rect()
        
    def on_key_down(self, key: int, unicode: str) -> None:
        """Called when a keyboard key is pressed."""
        pass

    def on_mouse_down(self, button: int) -> None:
        """
        Called when a mouse button is pressed.
        - 1 = left click
        - 2 = scroll wheel click
        - 3 = right click
        """
        pass

    def on_mouse_up(self, button: int) -> None:
        """Called when mouse button is released. See ``Screen.on_mouse_down``"""
        pass

    def on_scroll(self, dx: int, dy: int) -> None:
        """Called when mouse wheel is scrolled. Supports both horizontal and vertical scrolling."""
        pass

    def on_resize(self, new_res: Vec2) -> None:
        """Called when the window is resized, either by dragging the window or changing the window mode."""
        self.rect.size = new_res

    def kill(self) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass