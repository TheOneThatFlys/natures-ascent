from .node import Node

from .types import *

class Screen(Node):
    def __init__(self, parent: Node) -> None:
        super().__init__(parent)
        self.rect = parent.window.get_surface().get_rect()
        
    def on_key_down(self, key: int, unicode: str) -> None:
        pass

    def on_mouse_down(self, button: int) -> None:
        pass

    def on_scroll(self, dx: int, dy: int) -> None:
        pass

    def on_resize(self, new_res: Vec2) -> None:
        pass